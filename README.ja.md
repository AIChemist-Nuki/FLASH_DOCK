**🌐 Language / 言語:** [中文](README.md) | [English](README.en.md) | **日本語**

# FLASH_DOCK ⚡️

> AI による分子ドッキング統合プラットフォーム
>
> 🌐 多言語UI内蔵（中文 / English / 日本語）、サイドバーで切替

FLASH_DOCK は **リガンド準備 → ポケット検出 → ドッキング → 親和性予測** の
ワークフロー全体を、すぐ使える GUI にまとめた Streamlit アプリです。
[Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) をフォークし再構築しました。

---

## 本バージョン（by Nuki）の主な変更

| 変更点 | 内容 |
|--------|------|
| **ポケット検出を Pokeformer に** | P2Rank を [Pokeformer](https://github.com/pfnet-research/pocket_detection)（グラフTransformer + fpocket）に置換。アンサンブルスコアで並べた口袋と中心座標を出力。**Java 依存を廃止。** |
| **UI のモダン化** | 一貫した「科学計測器」デザイン：パイプライン段階ヘッダー、座標/スコアの等幅表示、アイコンナビ、カードUI。 |
| **すぐ動く · 単一環境** | 新しい `environment.yml`、`setup.sh` が**1つ**の conda 環境（アプリ + Pokeformer）を作り重みも自動取得。 |
| **コード整理** | 重複バナーや冗長 import を除去。`ui/`（テーマ+部品）と `pocket/`（Pokeformerアダプタ）を分離。 |
| **多言語 (i18n)** | 中 / 英 / 日、ワンクリック切替。翻訳は `lang/`。 |

> ロードマップ：スクリーニングをより大規模・高速に。まず **Apple MPS**、次に **NVIDIA CUDA**。推論デバイスは既に設定可能（CPU / MPS / CUDA）で、加速は今後のリリースで対応。

---

## 機能

| # | モジュール | 説明 |
|---|-----------|------|
| 1 | **リガンド準備** | SDFアップロード / 描画(Ketcher) / SMILES → 最適化3D配座（ETKDG + MMFF）、CSV一括対応 |
| 2 | **ポケット検出** | Pokeformer で結合ポケットを検出し、中心座標CSVを出力（単体 + 一括） |
| 3 | **ドッキング** | Uni-Mol Docking v2。ポケットCSVからグリッド自動入力、または手動設定 |
| 4 | **一括ドッキング** | 多タンパク質 × 多リガンドをバックグラウンド非同期実行、UUID追跡、ZIP出力 |
| 5 | **親和性予測** | PLANET による結合親和性予測、データ表示とヒートマップ生成 |
| 6 | **タスク管理** | バックグラウンドジョブの確認・DL・3D可視化 |

---

## アーキテクチャ：すべてを1つの環境で

プロジェクト全体が **単一 conda 環境 `flashdock`**（Python 3.10）を使い、UI と
Pokeformer ポケット検出が同じ環境を共有します。Pokeformer は分離と将来の加速の
ため、引き続き **サブプロセス** として呼び出します（Uni-Mol・PLANET と同じ）。

主な依存（すべて `environment.yml`）：`torch 2.5.x`、`PyG 2.5.3`、
`pytorch_scatter/cluster`、`fpocket 4.2`、`rdkit`、`streamlit`。

> torch 2.5.x の理由：Pokeformer は `pytorch_scatter/cluster` を必要とし、Apple
> Silicon では conda-forge のみが提供、かつ `torch<2.6` と安定して組み合わせ可能
> （2.5.x は `torch.load` の安全な既定も維持し MPS も同梱）。1つの環境でアプリと
> Pokeformer の両方を満たせる最新版です。

---

## クイックスタート

### 前提
- **conda または mamba**（[Miniforge](https://github.com/conda-forge/miniforge) 推奨）
- **Python 3.9+**
- GPU は任意：NVIDIA CUDA は自動有効、Apple Silicon は MPS/CPU

> Java は不要になりました — ポケット検出は fpocket を使用（`setup.sh` が隔離環境に導入）。

```bash
git clone https://github.com/AIChemist-Nuki/FLASH_DOCK.git
cd FLASH_DOCK
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` は `environment.yml` から単一環境 `flashdock`（アプリ + Pokeformer + fpocket）を作成し、
Uni-Core（ドッキング用）をベストエフォートで導入、Pokeformer の重みを Zenodo から取得（約396MB）、
Uni-Mol 重みを配置して `http://localhost:8501` で起動します。

2回目以降：`conda activate flashdock && streamlit run app.py`。

---

## モデルファイル

| モデル | サイズ | 同梱 | 用途 | 入手 |
|--------|--------|------|------|------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ 要DL | ドッキング | [Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases) |
| `fold0~4_best_model.pt` | 約396MB | ❌ 要DL | ポケット(Pokeformer) | Zenodo [10.5281/zenodo.13070037](https://doi.org/10.5281/zenodo.13070037)（`setup.sh`が自動取得） |
| `PLANET.param` | 18MB | ✅ 同梱 | 親和性 | — |

---

## 手動インストール

<details><summary>展開</summary>

```bash
# 1. 単一環境（torch / PyG / scatter+cluster / fpocket / rdkit / streamlit）
conda env create -f environment.yml && conda activate flashdock

# 2. ドッキングは Uni-Core（親和性は DGL）が必要 — 必要に応じて導入
pip install ninja && pip install ./others/Uni-Core

# 3. 重み
#  - Uni-Mol -> others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt
#  - Pokeformer: Zenodo の best_models.tar.xz を DL し fold0~4_best_model.pt を
#    others/pocket_detection/examples/ に展開

# 4. 起動
streamlit run app.py
```

</details>

---

## ワークフロー

**リガンド準備 → ポケット検出 → ドッキング →（一括）→ 親和性。**
サンプルはホーム画面から取得できます。

1. **リガンド準備** — SDF / Ketcher / SMILES → 最適化3D SDF。一括は `mol_name`, `smiles` 列のCSV。
2. **ポケット検出** — PDBをアップロード。単体は `best_pocket.csv`、一括は `Protein File / rank / center_x/y/z` のCSV（一括ドッキングにそのまま使える）を出力。中心は fpocket のポケット幾何から、並びは Pokeformer のアンサンブルスコア。
3. **ドッキング** — タンパク質 + リガンドをアップロード。ポケットCSVでグリッド自動入力、または手動設定。可視化とDL。
4. **一括ドッキング** — 一括ポケットCSV + 全タンパク質/リガンドをアップロード。`Run`列を編集して送信し、**ジョブID**を控える（バックグラウンド実行）。
5. **タスク管理 / 親和性** — ジョブ状態（✅/🔄/❌）を確認・DL・可視化。PLANET で親和性予測とヒートマップ。

---

## FAQ

- **fpocket / 重みが無い？** `setup.sh` か `environment.yml` で `flashdock` を作成し、`others/pocket_detection/examples/` に `fold0~4_best_model.pt` があるか確認。別環境で Pokeformer を動かす場合は `FLASHDOCK_POCKET_PYTHON` で上書き可能。
- **ドッキングが遅い？** Uni-Mol は CPU だと遅い。CUDA GPU 推奨（Apple加速は今後）。
- **ジョブが `running` のまま？** ターミナルを確認。多くは重み欠如やパス誤り。
- **Uni-Core のビルド失敗？** まず `pip install ninja`、torch/CUDA を一致させ、`--no-build-isolation` も試す。

---

## 使用しているAIアルゴリズム

| アルゴリズム | 用途 | 論文 / リポジトリ |
|--------------|------|-------------------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | ドッキング | Towards Accurate and Efficient Molecular Docking |
| [Pokeformer](https://github.com/pfnet-research/pocket_detection) | ポケット検出 | Ishitani et al., *Protein ligand binding site prediction using graph transformer neural network* |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | 親和性予測 | Protein-Ligand Binding Affinity Prediction |

---

## プロジェクト構成

```
FLASH_DOCK/
├── app.py                    # 起動：streamlit run app.py
├── environment.yml           # 単一 conda 環境（アプリ + Pokeformer）
├── requirements.txt          # pip 層（参考）
├── setup.sh                  # 一括インストール&起動
├── .streamlit/config.toml    # テーマ
├── ui/theme.py               # テーマ + 部品
├── pocket/pokeformer.py    # Pokeformer アダプタ
├── lang/                     # i18n (zh / en / ja)
├── Batch_Docking/ · examples/
└── others/                   # Uni-Mol · pocket_detection · PLANET · Uni-Core
```

---

## 謝辞

[Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) · [Uni-Mol](https://github.com/deepmodeling/Uni-Mol) · [Pokeformer (Preferred Networks)](https://github.com/pfnet-research/pocket_detection) · [PLANET](https://github.com/ComputArtCMCG/PLANET) · [fpocket](https://github.com/Discngine/fpocket) · [Streamlit](https://streamlit.io/)

## 作者

**原作者:** 小闪电-FLASH (Neo-Flash) · [GitHub](https://github.com/Neo-Flash)
**改修:** Nuki · 東京科学大学 · ma240306@tmd.ac.jp

## License
[Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) をベースに改修。Pokeformer は MIT。各上流プロジェクトのライセンスに従ってください。
