"""Pokeformer adapter — drop-in replacement for the old P2Rank pocket step.

Pokeformer (https://github.com/pfnet-research/pocket_detection, vendored at
``others/pocket_detection``) detects candidate pockets with **fpocket** and
ranks them with a 5-fold graph-transformer ensemble. It pins an older/separate
stack (torch / PyG) that conflicts with the main app, so we run it as a
**subprocess inside its own conda env** (default: ``flashdock-pocket``) — the
same pattern the app already uses for Uni-Mol and PLANET.

This module post-processes Pokeformer's output into the *exact* schema the
docking pages already consume, so nothing downstream changes:

* single protein  ->  ``predict_single()`` returns ``{name, center, rank, score}``
* batch / CSV     ->  ``predict_pockets()`` returns a DataFrame with columns
  ``Protein File, rank, score, pred_std, volume, center_x, center_y, center_z,
  Center, Pocket Name`` (a superset that satisfies both the single-docking
  ``Pocket Name``/``Center`` reader and the batch reader that needs
  ``protein file``/``rank``/``center_x|y|z``).

Pocket centers are the centroids of fpocket alpha-sphere vertices
(``pockets/<name>/in_out/pockets/pocketN_vert.pqr``); ranking is by the
ensemble score ``pred_aver`` (higher = better).
"""

from __future__ import annotations

import os
import re
import sys
import shutil
import subprocess
import tempfile
from importlib.util import find_spec
from pathlib import Path

import pandas as pd

# --- locations -------------------------------------------------------------
# repo root = parent of this file's package directory
_REPO_ROOT = Path(__file__).resolve().parent.parent
POCKET_REPO = _REPO_ROOT / "others" / "pocket_detection"
POCKET_EXAMPLES = POCKET_REPO / "examples"
DEFAULT_ENV = "flashdock"
MODEL_FILES = [f"fold{i}_best_model.pt" for i in range(5)]


class PokeformerError(RuntimeError):
    """Raised when Pokeformer cannot be run or produced no usable pocket."""


# --- environment / executable resolution -----------------------------------
def _conda_base() -> str | None:
    base = os.environ.get("CONDA_PREFIX_1") or os.environ.get("CONDA_PREFIX")
    if base and (Path(base) / "envs").exists():
        return base
    try:
        out = subprocess.run(
            ["conda", "info", "--base"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:
        return None


def _current_env_can_run() -> bool:
    """True if the interpreter running the app already has Pokeformer's deps."""
    return find_spec("torch_geometric") is not None and shutil.which("fpocket") is not None


def pocket_python(env_name: str = DEFAULT_ENV) -> str:
    """Return the python interpreter that can run Pokeformer.

    Resolution order:
      1. ``FLASHDOCK_POCKET_PYTHON`` env var (explicit override);
      2. the current interpreter, if it already has the deps (unified env);
      3. the named conda env ``env_name``;
      4. ``python`` (let ``conda run`` resolve it).
    """
    override = os.environ.get("FLASHDOCK_POCKET_PYTHON")
    if override:
        return override
    if _current_env_can_run():
        return sys.executable
    base = _conda_base()
    if base:
        cand = Path(base) / "envs" / env_name / "bin" / "python"
        if cand.exists():
            return str(cand)
    return "python"


def _python_cmd(env_name: str) -> list[str]:
    py = pocket_python(env_name)
    if py == "python":  # could not resolve a concrete interpreter
        return ["conda", "run", "--no-capture-output", "-n", env_name, "python"]
    return [py]


def weights_present() -> bool:
    return all((POCKET_EXAMPLES / m).exists() for m in MODEL_FILES)


# --- PDB cleaning -----------------------------------------------------------
def clean_pdb(src: str | Path, dst: str | Path) -> None:
    """Write a Pokeformer-ready copy: keep protein atoms, drop waters/hetero.

    Pokeformer expects PDBs with waters, ligands and non-amino-acid residues
    removed. We keep ATOM records (and TER), drop HETATM/HOH, which is a safe
    superset for standard structures.
    """
    with open(src, "r", errors="ignore") as fin, open(dst, "w") as fout:
        for ln in fin:
            rec = ln[:6]
            if rec.startswith(("ATOM", "TER", "ENDMDL", "MODEL", "END")):
                fout.write(ln)
            # HETATM (waters, ligands, ions, modified residues) intentionally dropped


# --- output parsing ---------------------------------------------------------
def _pqr_centroid(pqr_path: Path) -> tuple[float, float, float]:
    xs = ys = zs = 0.0
    n = 0
    with open(pqr_path) as f:
        for ln in f:
            if ln.startswith("ATOM  "):
                xs += float(ln[30:38])
                ys += float(ln[38:46])
                zs += float(ln[46:54])
                n += 1
    if n == 0:
        raise PokeformerError(f"empty pocket vertex file: {pqr_path}")
    return xs / n, ys / n, zs / n


def _parse_pocket_geometry(pdb_pockets_dir: Path) -> dict[int, dict]:
    """Map fpocket pocket_id -> {volume, center_x, center_y, center_z}."""
    out_dir = pdb_pockets_dir / "in_out"
    info_file = out_dir / "in_info.txt"
    if not info_file.exists():
        raise PokeformerError(f"missing fpocket info file: {info_file}")

    volumes: dict[int, float] = {}
    pkt_id = None
    for ln in info_file.read_text().splitlines():
        m = re.match(r"Pocket (\d+) :", ln)
        if m:
            pkt_id = int(m.group(1))
            continue
        m = re.match(r"\s+Volume\s*:\s*([\d.\-\+eE]+)", ln)
        if m and pkt_id is not None:
            volumes[pkt_id] = float(m.group(1))

    geom: dict[int, dict] = {}
    pockets_dir = out_dir / "pockets"
    for pkt_id, vol in volumes.items():
        pqr = pockets_dir / f"pocket{pkt_id}_vert.pqr"
        if not pqr.exists():
            continue
        cx, cy, cz = _pqr_centroid(pqr)
        geom[pkt_id] = {
            "volume": vol,
            "center_x": cx,
            "center_y": cy,
            "center_z": cz,
        }
    return geom


def _match_rows_to_pockets(rows: pd.DataFrame, geom: dict[int, dict]) -> pd.DataFrame:
    """Attach center coordinates to each scored pocket row via volume match.

    Pokeformer's CSV gives (volume, pred_aver) per pocket but no center.
    fpocket's geometry gives (volume, center) per pocket_id. Volumes come from
    the same source, so we match each row to its pocket_id by nearest volume
    (order-independent and robust).
    """
    available = dict(geom)  # pocket_id -> geom, consumed as matched
    records = []
    for _, row in rows.iterrows():
        vol = float(row["volume"])
        if not available:
            break
        pkt_id = min(available, key=lambda k: abs(available[k]["volume"] - vol))
        g = available.pop(pkt_id)
        records.append(
            {
                "pocket_id": pkt_id,
                "score": float(row.get("pred_aver", float("nan"))),
                "pred_std": float(row.get("pred_std", float("nan"))),
                "volume": g["volume"],
                "center_x": g["center_x"],
                "center_y": g["center_y"],
                "center_z": g["center_z"],
            }
        )
    return pd.DataFrame(records)


# --- main entry points ------------------------------------------------------
def run_pokeformer(
    pdb_paths: list[str | Path],
    workdir: str | Path,
    env_name: str = DEFAULT_ENV,
    gpu: int = -1,
    do_clean: bool = True,
) -> tuple[Path, Path, dict[str, str]]:
    """Run Pokeformer inference on one or more PDB files.

    Returns ``(infer_csv, pockets_base, name_map)`` where ``name_map`` maps the
    safe basename used for inference back to the caller's original filename.
    """
    if not weights_present():
        raise PokeformerError(
            "Pokeformer model weights not found in "
            f"{POCKET_EXAMPLES}. Download best_models.tar.xz from Zenodo "
            "(10.5281/zenodo.13070037) and extract the fold*_best_model.pt files "
            "there — see setup.sh / README."
        )

    workdir = Path(workdir)
    inputs_dir = workdir / "inputs"
    pockets_base = workdir / "pockets"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    pockets_base.mkdir(parents=True, exist_ok=True)
    infer_csv = workdir / "infer_results.csv"

    # Copy/clean inputs to safe, space-free names; remember the mapping.
    safe_paths: list[Path] = []
    name_map: dict[str, str] = {}
    for i, p in enumerate(pdb_paths):
        p = Path(p)
        safe = inputs_dir / f"prot_{i}.pdb"
        if do_clean:
            clean_pdb(p, safe)
        else:
            shutil.copyfile(p, safe)
        safe_paths.append(safe.resolve())
        name_map[safe.name] = p.name

    pdb_list = "[" + ",".join(str(p) for p in safe_paths) + "]"
    model_list = "[" + ",".join(MODEL_FILES) + "]"

    cmd = _python_cmd(env_name) + [
        str((POCKET_REPO / "scripts" / "inference.py").resolve()),
        "yaml=config_pdbinfer.yaml",
        f"sampler.gpu={gpu}",
        f"sampler.model_path_list={model_list}",
        f"sampler.out_csv={infer_csv.resolve()}",
        f"sampler.pdb_files={pdb_list}",
        f"sampler.pocket_result_base={pockets_base.resolve()}/",
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(POCKET_REPO.resolve())
    # Invoking the env's python directly does not activate the env, so its bin/
    # (where the `fpocket` binary lives) is not on PATH. Prepend it.
    py = pocket_python(env_name)
    if py != "python":
        env["PATH"] = str(Path(py).parent) + os.pathsep + env.get("PATH", "")

    proc = subprocess.run(
        cmd,
        cwd=str(POCKET_EXAMPLES.resolve()),  # so config + vocab + weights resolve
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not infer_csv.exists():
        raise PokeformerError(
            "Pokeformer inference failed.\n"
            f"command: {' '.join(cmd)}\n"
            f"stderr (tail):\n{proc.stderr[-2000:]}"
        )
    return infer_csv, pockets_base, name_map


def predict_pockets(
    pdb_paths: list[str | Path],
    original_names: list[str] | None = None,
    env_name: str = DEFAULT_ENV,
    gpu: int = -1,
    workdir: str | Path | None = None,
) -> pd.DataFrame:
    """Predict and rank pockets for one or more proteins.

    Returns a DataFrame (one row per pocket, ranked per protein) with columns:
    ``Protein File, rank, score, pred_std, volume, center_x, center_y,
    center_z, Center, Pocket Name``.
    """
    pdb_paths = [Path(p) for p in pdb_paths]
    if original_names is None:
        original_names = [p.name for p in pdb_paths]

    tmp_ctx = None
    if workdir is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="pokeformer_")
        workdir = tmp_ctx.name
    try:
        infer_csv, pockets_base, _ = run_pokeformer(
            pdb_paths, workdir, env_name=env_name, gpu=gpu
        )
        df = pd.read_csv(infer_csv)

        # PDB_ID is the (absolute) safe path we passed; group by its basename.
        df["__base"] = df["PDB_ID"].map(lambda s: Path(str(s)).name)

        # map safe basename ("prot_<i>.pdb") -> caller's original filename
        safe_name_by_index = {
            f"prot_{i}.pdb": original_names[i] for i in range(len(original_names))
        }

        all_rows = []
        for safe_base, group in df.groupby("__base"):
            orig_name = safe_name_by_index.get(safe_base, safe_base)
            pdb_pockets_dir = pockets_base / safe_base
            geom = _parse_pocket_geometry(pdb_pockets_dir)
            matched = _match_rows_to_pockets(group, geom)
            if matched.empty:
                continue
            matched = matched.sort_values(
                "score", ascending=False, kind="stable"
            ).reset_index(drop=True)
            matched.insert(0, "rank", range(1, len(matched) + 1))
            matched.insert(0, "Protein File", orig_name)
            all_rows.append(matched)

        if not all_rows:
            raise PokeformerError("Pokeformer found no pockets for the input(s).")

        result = pd.concat(all_rows, ignore_index=True)
        result["Center"] = result.apply(
            lambda r: f"{r['center_x']:.3f}, {r['center_y']:.3f}, {r['center_z']:.3f}",
            axis=1,
        )
        result["Pocket Name"] = result["Protein File"]
        return result
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


def predict_single(
    pdb_path: str | Path,
    name: str | None = None,
    env_name: str = DEFAULT_ENV,
    gpu: int = -1,
) -> dict:
    """Predict pockets for one protein, return the best pocket.

    Mirrors the old ``select_pocket_from_local_protein`` return shape:
    ``{"name", "center", "rank", "score", "all": DataFrame}``.
    """
    name = name or Path(pdb_path).name
    df = predict_pockets([pdb_path], [name], env_name=env_name, gpu=gpu)
    best = df.iloc[0]
    return {
        "name": name,
        "center": best["Center"],
        "rank": int(best["rank"]),
        "score": float(best["score"]),
        "all": df,
    }


if __name__ == "__main__":  # tiny manual smoke test
    import sys

    paths = sys.argv[1:] or [str(POCKET_EXAMPLES / "1SQN.pdb")]
    out = predict_pockets(paths)
    pd.set_option("display.width", 160)
    print(out.to_string(index=False))
