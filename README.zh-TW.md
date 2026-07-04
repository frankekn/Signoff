# Traction

> **Coding agent 的 traction layer。**你只要說出想看到的成果；Traction 負責 Push 審議、鎖定目標、限制每輪建置、執行可驗證證據、Pull 獨立審查，然後前進一格——附帶證明。

Traction 是包在現有 coding agent 外面的本機開源 push-pull 引擎。它不是另一個模型、IDE、工作流語言，也不是讓多個 agent 自由聊天的聊天室。

命名刻意維持簡單：

- **Traction** 是產品與 repository 名稱。
- **Grip** 是 Traction 內部的 deterministic 引擎；agent 可以提案與質疑，但只有 Grip 能推進狀態。
- **Traction Protocol** 是版本化的 artifact、hash、角色邊界與合法 transition。
- **Receipt** 是每個 accepted slice 或 completed run 產出的可重播證據包。

```text
使用者成果
  → 可證偽規格
  → Push 審議
  → hash lock
  → 一個 bounded slice
  → executable evidence
  → Pull 審查
  → SIGNED OFF / REWORK / STOPPED / PIVOT / BLOCKED
```

## Push-pull 引擎

Traction 的設計目標是收斂而非振盪：

1. **Push**（鎖定前規劃審議）→ **lock** → **build** → **Pull**（對照鎖定合約審查）→ **前進一格**。Pull 只能朝鎖定目標收斂——審查者的品味或新點子不算驗收失敗——因此迴圈會前進而不是來回搖擺。

2. **真實的 mixture-of-agents 集體提供品質。** Push 與 Pull 預設 ≥2 個真正異質的 advisor（不同 provider/model，由 host agent 平行派送）。單人模式是降級狀態，必須誠實標記 `INSUFFICIENT_QUORUM`。只有 aggregator 負責綜合並寫入 artifact（Push 的 chair、Pull 的 judge）；不投票、不平均；實質衝突只能由實驗、既有證據、locked spec 或使用者決定關閉。外部證據：NousResearch 的 HermesBench 報告 opus-4.8 aggregator 搭配 gpt-5.5 reference 為 0.8202，對比單獨 opus 的 0.7607——那是他們的結果，不是 Traction 的。

3. **棘輪鎖住集體決定的標準。** Hash-locked goal、charter、spec 與 contract 代表實作前同意的標準不能在事後悄悄改寫。可執行驗證是 Pull 對照的 oracle。

## 兩個指令開始

需求只有 **Git** 與 **Python 3.10+**：

```sh
./install.sh
./traction ui
```

開啟 `http://127.0.0.1:8765`，輸入成果，就能從 UI 控制並觀測整個 run。

Repo 內附一次性 demo：

```sh
./scripts/demo.sh
```

Demo 會建立隔離的範例 repository，停在可實作的 slice。修改 `app.py` 後，就能從 UI 執行驗證。

### 安裝到另一個 repository

```sh
/path/to/traction/install.sh /path/to/your/repository
cd /path/to/your/repository
./traction ui
```

Windows PowerShell：

```powershell
.\install.ps1 C:\path\to\your\repository
cd C:\path\to\your\repository
.\traction.ps1 ui
```

Release 已內含編譯完成的 UI。一般使用者不需要 Node.js、npm、Docker、雲端帳號或 global install。

## 直接貼給任何 coding agent

```text
把 <GITHUB_REPOSITORY_URL> 的 Traction 安裝進目前 repository。
用它完成這個精確成果：<用一般語言描述成果>。
先讀 AGENTS.md，再執行 ./traction status 與 ./traction next，每次只做唯一合法的下一步。
不得修改 locked artifacts 或 generated receipts；Traction 沒有回傳 DONE 就不能宣稱完成。
```

## UI 能做什麼

- 用一句話開始 run；
- 永遠只顯示一個合法下一步；
- 只允許編輯目前 phase 合法的 artifact；
- 執行 scope check、verification、Pull review、pivot 與終態完成；
- 查看 immutable goal、contract、evidence、patch receipt 與 hash-chained timeline。

前端使用 Vite、React、TanStack Router 與 TanStack Query；建置後由零第三方相依的 Python runtime 提供本機 API 與靜態頁面。

## 為什麼不只是編排

Prompt 寫「不要 drift」並不會改變 agent 同時控制規格、測試、review 與完成宣告的權力結構。Traction 把這些權力移到 machine-enforced gates。

| 常見失敗 | 結構性控制 |
|---|---|
| 目標被悄悄重寫 | 原始句子逐字保存並綁定 hash |
| 實作後移動 acceptance criteria | Charter、Spec、Push 決策與 Contract 鎖定 |
| Agent 自己改、自己評分 | Builder、reviewer、judge 必須是不同 identity/context |
| Advisor 各答各的 | Push advisor 回傳 route、falsifiable criteria、risk、first move、cut；實質衝突以 verdict 分裂辨識 |
| 共識取代事實 | 衝突只能由實驗、既有證據、locked spec 或使用者決定關閉 |
| 只在文字裡說測試通過 | Runtime 親自執行 command 並保存 exit code 與 output hash |
| 順手整理造成 scope creep | Git baseline、allowed paths、檔案數與 changed-line budget |
| 測試偷偷改 patch | Verification 過程改變 patch 就失敗 |
| Reviewer 發明新需求 | Finding 必須 disposition；規格外工作維持 out of scope |
| `UNKNOWN` 被包裝成 PASS | 未解 uncertainty 不能得到 SIGNED OFF |
| 流程永遠跑不完 | Iteration 與重複 root cause 強制 pivot 或 stop |
| Receipt 事後被改 | Artifact hash 與 append-only ledger 會重新驗證 |

初始版先把可靠的 control boundary 做好，不假裝已完成 universal hidden-oracle synthesis 或全自動 provider routing。

## 常用 CLI

```sh
./traction ui
./traction doctor
./traction start "新增 Google 登入，但不能改變既有 email 登入行為"
./traction status
./traction next
./traction prepare-push
./traction lock
./traction prepare-slice
./traction slice
./traction check-scope
./traction verify
./traction prepare-pull
./traction pull
./traction finish accepted
./traction finish done
./traction finish rework --root-cause "缺少負向路徑證據"
./traction pivot --reason "測試路線無法滿足鎖定成果"
./traction integrity
./traction benchmark
```

Run artifacts 位於 `.traction/runs/<run-id>/`。

## 如何證明有效

Traction 刻意分開兩個命題：

1. **Protocol conformance**：gate 是否真的會擋下 tampering、scope creep、fake quorum、self-review、證據不足與 false completion。
2. **Real-agent efficacy**：在相同模型、權限、時間與成本下，Traction 是否比 agent alone 與 prompt-only loop 更少 false completion、更多 held-out success。

```sh
python3 scripts/test.py
```

Alpha 階段只會誠實宣稱 deterministic gates 的測試結果，不會在 controlled held-out experiment 前宣稱真實 coding success 已提升。詳見 [`docs/benchmarks.md`](docs/benchmarks.md)。

## 開發

一般使用者不需要 Node。修改 UI 的貢獻者使用 Node 22.12+：

```sh
npm ci
npm run typecheck
npm run build:web
python3 scripts/test.py
python3 scripts/check_repo.py
```

Runtime 維持 Python standard library only。`src/traction/web_dist/` 必須與 production build 一致。

## Repository layout

```text
apps/web/                 Vite + React + TanStack 原始碼
src/traction/             零相依 runtime、本機 API、打包 UI
skills/                   traction 與 loop agent skills
protocol/schemas/         文件化的 JSON artifact 介面
tests/                    對抗性 conformance 與 API 測試
bench/                    受控 real-agent efficacy harness
scripts/                  安裝、demo、檢查與 release 工具
```

## 安全邊界

Traction 會執行 repository 宣告的 verification commands；請把它們視為程式碼。不信任的 repository 必須放進 OS/container sandbox，UI 預設只綁定 localhost。

Local alpha 是 tamper-evident，不是 secure enclave。詳見 [`SECURITY.md`](SECURITY.md) 與 [`docs/threat-model.md`](docs/threat-model.md)。

Apache-2.0 授權。
