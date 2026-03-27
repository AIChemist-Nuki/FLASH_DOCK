**🌐 Language / 言語:** [中文](README.md) | [English](README.en.md) | **日本語**

# FLASH_DOCK ⚡️

> AI駆動型オールインワン分子ドッキングプラットフォーム | AI-Powered Molecular Docking Platform
>
> 🌐 アプリ内で多言語対応（中文 / English / 日本語）— サイドバーで切り替え可能

FLASH_DOCK は、Streamlit で構築された計算化学 Web アプリケーションです。リガンド準備、ポケット予測、分子ドッキング、結合親和性予測などの機能を統合し、医薬品発見研究向けのすぐに使用できるグラフィカルインターフェースを提供します。

本プロジェクトは [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) からフォークされており、元のバージョンをベースに機能拡張と最適化を行っています。

---

## 元のバージョンとの主な相違点

このバージョン（by Nuki）は、元のバージョンをベースに以下の内容を追加・最適化しました：

| 変更項目 | 説明 |
|--------|------|
| **タスク管理モジュール** | 新しい「タスク管理」ページで、すべてのバックグラウンドドッキングタスクのステータス（完了/実行中/失敗）を確認でき、時間または名前でソート可能、結果パッケージを直接ダウンロードして3D可視化を表示できます |
| **バッチドッキング結果の可視化** | バッチ分子ドッキングページに3D可視化機能を新たに追加し、タンパク質PDBとリガンドSDFを自動マッチングして表示します |
| **タスク数制限** | バッチドッキングタスク数の上限チェック（200個）を新たに追加し、サーバー過負荷を回避します |
| **タスクログの強化** | 各ドッキングタスクに詳細な実行ログがあり、座標情報、成功/失敗ステータスを記録します |
| **多言語サポート (i18n)** | 中文/英語/日本語の3言語サポートを新たに追加し、サイドバーで1クリック切り替え可能、翻訳ファイルは `lang/` ディレクトリにあり、新言語の追加は簡単です |
| **コード構造の最適化** | パスワード埋め込みを削除してコード構造を再構築し、コードがより明確で読みやすくなりました |

---

## 機能概要

FLASH_DOCK は **6 つの機能モジュール** を提供し、リガンド準備から親和性分析までの完全なワークフローをカバーしています：

### 1. リガンド準備
SDF ファイルをアップロード、オンラインで分子を描画（Ketcher）、または SMILES を直接入力して、最適化された 3D 構象を自動生成（ETKDG + MMFF 力場）します。CSV ファイル内の SMILES データのバッチ処理に対応しています。

### 2. ポケット予測
P2Rank アルゴリズムに基づいてタンパク質結合ポケットを自動予測し、単一および複数タンパク質予測に対応、ポケット中心座標の CSV ファイルを出力して、その後のドッキングに直接使用できます。

### 3. 分子ドッキング
Uni-Mol Docking v2 モデルに基づき、タンパク質（PDB）とリガンド（SDF）をアップロードすると、ポケット予測 CSV を自動読み込みしてドッキングパラメータを入力、またはドッキングボックスを手動で調整することもできます。

### 4. バッチ分子ドッキング
複数タンパク質 × 複数リガンドのバッチドッキング、バックグラウンド非同期処理でページをブロックしない、UUID タスク ID で追跡、結果を自動的に ZIP ファイルにパッケージ化します。

### 5. 結合親和性予測
PLANET モデルに基づいて結合親和性を予測し、単一および複数予測に対応、3 つのタブ：親和性予測 / データ表示 / ヒートマップ生成があります。

### 6. タスク管理（新機能）
すべてのバックグラウンドドッキングタスクを集中管理、ステータスアイコン（✅🔄❌）、時間/名前でソート、結果パッケージを1クリックでダウンロード、ドッキング結果を3D可視化できます。

---

## クイックスタート（ワンクリック インストール）

### 前提条件

開始する前に、システムに以下がインストールされていることを確認してください：
- **Python 3.8+**
- **Java 8+**（P2Rank ポケット予測に必要。インストール方法：Ubuntu `sudo apt install default-jdk` / macOS `brew install openjdk`）
- **CUDA GPU**（オプションですが、ドッキング計算を大幅に高速化するため強く推奨）

### インストール手順

```bash
# 1. プロジェクトをクローン
git clone https://github.com/AIChemist-Nuki/FLASH_DOCK.git
cd FLASH_DOCK

# 2. Uni-Mol Docking v2 モデルウェイトをダウンロード（約 465MB）
#    ダウンロードURL: https://github.com/deepmodeling/Uni-Mol/releases
#    unimol_docking_v2_240517.pt を見つけて任意の場所にダウンロード

# 3. 仮想環境を作成（推奨）
conda create -n flashdock python=3.9 -y
conda activate flashdock

# 4. ワンクリック インストールと起動（モデルウェイトパスを指定）
bash setup.sh /path/to/unimol_docking_v2_240517.pt
```

`setup.sh` は以下のすべてを自動的に完了します：
- システム環境をチェック（Python、Java、CUDA）
- モデルウェイトを正しい場所にコピー
- PyTorch をインストール（CUDA/CPU に自動適応）
- Uni-Core フレームワークをコンパイルしてインストール
- すべての Python 依存関係をインストール
- P2Rank と PLANET モデルをチェック
- インストール状態の概要を印字
- Streamlit アプリケーションを起動

起動に成功するとブラウザが自動的に `http://localhost:8501` を開きます。

### その後の起動

最初のインストール完了後、以降は以下を実行するだけです：

```bash
conda activate flashdock
bash setup.sh
```

スクリプトは既にインストールされた依存関係をスキップし、アプリケーションを直接起動します。

---

### 手動インストール（スクリプトが適用できない場合）

<details>
<summary>手動インストール手順をクリックして展開</summary>

#### 1. PyTorch をインストール

ハードウェア環境に応じて https://pytorch.org/get-started/locally/ からインストール コマンドを取得します：

```bash
# CUDA GPU がある場合:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# CPU のみの場合:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### 2. Uni-Core をインストール

```bash
pip install ninja
cd others/Uni-Core
pip install .
cd ../..
```

コンパイルエラーが発生した場合は、[Uni-Core 公式リポジトリ](https://github.com/dptech-corp/Uni-Core) を参照してください。

#### 3. その他の依存関係をインストール

```bash
pip install streamlit streamlit-molstar streamlit-ketcher py3Dmol stmol
pip install rdkit-pypi pandas numpy scipy scikit-learn matplotlib seaborn
pip install tqdm lmdb sh biopandas
```

#### 4. モデルウェイトを配置

ダウンロードした `unimol_docking_v2_240517.pt` を以下の場所に配置します：

```
others/Uni-Mol/unimol_docking_v2/unimol_docking_v2_240517.pt
```

#### 5. P2Rank が実行可能であることを確認

```bash
chmod +x others/p2rank_2.5/prank
```

#### 6. 起動

```bash
streamlit run FlashDock_0315.py
```

</details>

---

### モデルファイルの説明

| モデル | サイズ | リポジトリに含まれる？ | 用途 |
|------|------|----------------|------|
| `unimol_docking_v2_240517.pt` | 465MB | ❌ 自分でダウンロード | 分子ドッキング（コア機能） |
| `PLANET.param` | 18MB | ✅ 含まれています | 結合親和性予測 |
| `p2rank_2.5/` | 292MB | ✅ 含まれています | ポケット予測 |

Uni-Mol モデル ダウンロード URL：[Uni-Mol Releases](https://github.com/deepmodeling/Uni-Mol/releases)

---

## 使用チュートリアル

### 典型的なワークフロー

```
リガンド準備 → ポケット予測 → 分子ドッキング → 結合親和性予測
```

以下は、完全な分子ドッキング実験の例で、ワークフロー全体を説明します。プロジェクトにはサンプルファイルが含まれており、ホームページの「サンプルファイルをダウンロード」をクリックして取得できます。

---

### ステップ 1: リガンド準備

> 目的：小分子を最適化された 3D 構象を持つ SDF ファイルに変換する

**方法 A：SDF ファイルをアップロード**
1. サイドバーの「リガンド準備」をクリック
2. 「単分子処理」タブで SDF ファイルをアップロード
3. システムが自動的に 2D と 3D 分子構造を表示
4. 「3D分子のSDFファイルをダウンロード」をクリックして結果を保存

**方法 B：分子を描画または SMILES を入力**
1. Ketcher エディタで分子構造を描画、または SMILES 文字列を直接貼り付け
2. システムが自動的に 3D 構象を生成（ETKDG アルゴリズム + MMFF 力場最適化）
3. 生成された SDF ファイルをダウンロード

**方法 C：バッチ処理**
1. 「バッチ処理」タブに切り替え
2. SMILES 列を含む CSV ファイルをアップロード
3. システムがすべての分子の 3D 構造をバッチ生成
4. 結果をダウンロード

---

### ステップ 2: ポケット予測

> 目的：タンパク質上で小分子が結合する可能性が最も高い場所（ポケット）を見つける

**単一タンパク質：**
1. サイドバーの「ポケット予測」をクリック
2. 「単一タンパク質ポケット予測」を選択
3. タンパク質 PDB ファイルをアップロード（または「サンプルタンパク質を読み込む」で素早く体験）
4. システムが P2Rank を使用してポケット位置を予測
5. ポケット中心座標表を表示し、rank1 ポケットの座標を記録

**複数タンパク質：**
1. 「バッチタンパク質ポケット予測」を選択
2. 複数の PDB ファイルを一度にアップロード
3. 「バッチ予測を開始」をクリック
4. 要約されたポケット予測 CSV ファイルをダウンロード — **その後のバッチドッキングに必要なファイル**

---

### ステップ 3: 分子ドッキング

#### 単一ドッキング

1. サイドバーの「分子ドッキング」をクリック
2. タンパク質 PDB とリガンド SDF ファイルをアップロード
3. ドッキンググリッド パラメータを設定：
   - 以前ポケット予測を行った場合、CSV ファイルをアップロードして座標を自動入力
   - または、中心座標（center_x/y/z）とボックスサイズ（size_x/y/z）を手動で入力
4. 「ドッキングを開始」をクリック
5. 計算完了を待ちます（通常は数分）、3D 可視化結果を表示
6. ドッキング結果 SDF ファイルをダウンロード

#### バッチドッキング

1. サイドバーの「バッチ分子ドッキング」をクリック
2. 先ほど生成した**バッチポケット予測 CSV ファイル**をアップロード
3. すべてのタンパク質（PDB）とリガンド（SDF）ファイルをアップロード
4. システムが自動的にドッキング タスク リストを生成（各タンパク質 × 各リガンド = 1 つのタスク）
5. タスク CSV テンプレートをダウンロードし、`Run` 列を編集して `Yes/No` で実行対象を制御
6. 修正した CSV をアップロードして「バッチドッキングを開始」をクリック
7. **タスク ID を記憶** してください（形式：`a690c342`）、バックグラウンドで非同期実行

---

### ステップ 4: タスク表示と管理

**方法 A：「バッチ分子ドッキング」ページでクエリ**
1. ページ上部の「タスク クエリ」エリアにタスク ID を入力
2. ステータス、ログを表示、結果パッケージをダウンロード

**方法 B：「タスク管理」ページで一元管理**
1. サイドバーの「タスク管理」をクリック
2. すべての履歴タスク リストを表示（✅ 完了 / 🔄 実行中 / ❌ 失敗）
3. 時間または名前でソート
4. タスクを展開して詳細ログを表示
5. 結果 ZIP パッケージをダウンロード
6. 具体的なドッキング結果を選択して 3D 可視化

---

### ステップ 5: 結合親和性予測

> 目的：タンパク質-リガンドの結合強度を評価する

1. サイドバーの「予測親和性」をクリック
2. 「親和性予測」タブ内：
   - 単一予測：1 対の PDB + SDF ファイルをアップロード
   - バッチ予測：複数のタンパク質とリガンド ファイルをアップロード、システムはファイル名で自動マッチング
3. 「データ表示」タブ内：
   - 予測結果テーブルを表示
   - データ分布ヒストグラムとボックスプロット
   - CSV 結果をダウンロード
4. 「ヒートマップ生成」タブ内：
   - ヒートマップの色スキーム、サイズ、カラーバー範囲をカスタマイズ
   - タンパク質-リガンド親和性マトリックス ヒートマップを生成
   - ヒートマップ画像をダウンロード

---

## よくある質問

**Q: 起動後にページが空白または `ModuleNotFoundError` エラーが表示される**
A: 正しい仮想環境が有効化されているか確認し、すべての pip 依存関係がインストールされていることを確認してください。

**Q: ポケット予測が `java: command not found` エラーを報告する**
A: P2Rank は Java ランタイム環境に依存しているため、JDK 8 以上をインストールしてください。

**Q: ドッキング計算が非常に遅い**
A: Uni-Mol Docking v2 は CPU 上で実行すると遅く、CUDA GPU の使用を強く推奨します。GPU 上の単一ドッキング タスクは通常数分、CPU 上ではより長い時間がかかる場合があります。

**Q: バッチドッキング タスク ステータスが常に `running` と表示される**
A: ターミナルにエラー メッセージがないか確認してください。一般的な原因はモデル ファイルの欠落またはパス が不正です。

**Q: `Uni-Core` インストールが失敗**
A: `ninja` がインストールされていることを確認してください（`pip install ninja`）、PyTorch バージョンが CUDA バージョンと一致しているか確認してください。`pip install --no-build-isolation .` を試すこともできます。

---

## 使用される AI アルゴリズム

| アルゴリズム | 用途 | 論文 |
|------|------|------|
| [Uni-Mol Docking v2](https://arxiv.org/abs/2405.11769) | 分子ドッキング | Towards Accurate and Efficient Molecular Docking |
| [P2Rank](https://jcheminf.biomedcentral.com/articles/10.1186/s13321-018-0285-8) | ポケット予測 | P2Rank: machine learning based tool for rapid and accurate prediction of ligand binding sites |
| [PLANET](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00253) | 結合親和性予測 | Protein-Ligand Binding Affinity Prediction |

---

## プロジェクト構成

```
FLASH_DOCK/
├── FlashDock_0315.py              # メイン プログラム（最新バージョン、これを直接実行）
├── FlashDock_web.py               # オリジナル Web プログラム（参考用）
├── README.md
├── Batch_Docking/                 # バッチドッキング サンプル入力ファイル
│   ├── receptor1~4.pdb
│   └── ligand1~4.sdf
├── Result/                        # 単一実行結果出力ディレクトリ
│   ├── Binding_Affinity/
│   ├── Docking_Result/
│   ├── Predict_Pocket/
│   └── Prepare_Ligand/
├── jobs/                          # バックグラウンド タスク ディレクトリ（自動生成、クリア可能）
├── examples/                      # サンプル データ
│   └── examples.zip
└── others/                        # サード パーティ ツールとモデル
    ├── Uni-Mol/                   # Uni-Mol ドッキング モデル
    │   └── unimol_docking_v2/
    │       ├── interface/demo.py  # ドッキング エントリー スクリプト
    │       └── *.pt              # モデル ウェイト（ダウンロード必須）
    ├── PLANET/                    # 結合親和性予測 モデル
    │   ├── pred.py               # 予測 エントリー スクリプト
    │   └── PLANET.param          # モデル パラメータ（ダウンロード必須）
    ├── p2rank_2.5/                # ポケット予測 ツール
    │   └── prank                  # 実行可能ファイル（Java が必須）
    ├── Uni-Core/                  # PyTorch 基盤フレームワーク
    ├── flashdock.png              # アプリケーション ロゴ
    ├── author.png                 # 元作者情報
    └── author2.png                # 貢献者情報
```

---

## 謝辞

- オリジナル プロジェクト作成者：[小闪电-FLASH (Neo-Flash)](https://github.com/Neo-Flash/FLASH_DOCK)
- [Uni-Mol Docking v2](https://github.com/deepmodeling/Uni-Mol) - 分子ドッキング エンジン
- [P2Rank](https://github.com/rdk/p2rank) - ポケット予測 ツール
- [PLANET](https://github.com/ComputArtCMCG/PLANET) - 結合親和性予測 モデル
- [Streamlit](https://streamlit.io/) - Web アプリケーション フレームワーク

---

## 作成者および貢献者

**元作者**: 小闪电-FLASH (Neo-Flash)
華東理工大学 薬学部 | 華東師範大学 コンピュータ科学・テクノロジー学部
Email: 52265901016@stu.ecnu.edu.cn
GitHub: [Neo-Flash](https://github.com/Neo-Flash)

**修正と最適化**: Nuki
東京医科歯科大学 (2023-2024) | 東京科学大学 (2024-2026)
Email: ma240306@tmd.ac.jp

---

## ライセンス

このプロジェクトは [Neo-Flash/FLASH_DOCK](https://github.com/Neo-Flash/FLASH_DOCK) を修正しています。元のプロジェクトのライセンス契約に従ってください。
