## FastAPI
起動: uvicorn app.main:app --reload

## alembic
- alembic revision --autogenerate -m "initial schema" -> マイグレーションファイル作成(alembic/versions/)
- alembic upgrade head -> マイグレート

## SQLite
- sqlite3 dev.db
- .tables
- schema users; // 
- .quit // 終了

## Test
- python -m pytest {指定したいパスがあればいれる}

## domain/model層 判断基準
domain 層は、「このシステムでのビジネスルールをまとめた“ルールブック”」。
application 層は、「ルールブックを見ながら、どの順番で何をするかを決める司令塔」。
infrastructure 層は、「司令塔に言われたことを、DBや外部サービスを使って実際にやる人たち」。

### 実務でどう判断すればいいか？
- ビジネス側の人（PM, 顧客担当）が知っておきたい情報か？
  - はい → ドメインに入れる候補
  - いいえ（技術的な都合だけ）→ インフラ/アプリケーション側だけでOK

- この値が変わったときに、何かビジネスルールが動くか？
  - 例：status が LOST になると「これ以上商談作れない」とか
  - 何かの「ルールの if 判定」に関係するならドメイン

- このフィールドを使って「意味のあるメソッド」を書けそうか？
  - 例：can_create_opportunity, mark_lost, assign_to(user) など
  - ただのログ用・トレース用ならドメインに載せなくてもいい

- 「画面で今は使うかどうか」とは切り離して考える
  - 画面の表示は DTO の話
  - ドメインは「このシステムでどういう顧客を扱うか」の話

### domainの顧客に「DBに存在しない値」を入れることはあるか
ある。例えば：「この顧客はVIPかどうか」
定義：直近1年の売上が100万円以上ならVIP
DBには is_vip カラムを作らず、売上履歴テーブルなどから計算して Customer のプロパティとして持つ

```
@dataclass
class Customer:
    id: int
    total_sales_last_year: int  # ← 他テーブルから集計して渡す
    # ...他の属性...

    @property
    def is_vip(self) -> bool:
        return self.total_sales_last_year >= 1_000_000
```

is_vip は DBカラムじゃない
でもビジネスルール的には重要な概念（「この顧客はVIP扱いにするか？」）

### 各Classの分け方(ex: Customer)
- domain/Customer
  - 「このシステムにおける顧客とは何者か」
- application/CustomerSummary(ユースケース)
  - 「顧客一覧ユースケースがアプリ内部で扱う“行データ”」
- interface(FastAPI) のレスポンスモデル
  - 単純に「HTTP で返す JSON の形」（BaseModel）
- infrastructure/orm/customer
  - DB値


## domain層
① domain 層 = 会社の「ルールブック」
「このシステムの中での 顧客 って、どういう存在？」
「どんな状態の顧客に、どんな操作をしてもいい / ダメ？」
「商談は、どのステータスからどのステータスに遷移できる？」
みたいな、ビジネスとして大事なルールだけ が書いてある場所です。

### domain 層があることで何が嬉しいのか（非エンジニア視点）
### 1. 変更に強くなる（ビジネスが変わってもシステムが死なない）
例：SFA 現場でよくある変更
「ACTIVE の顧客にしか新規商談を作っちゃダメ」というルールが追加された
「LOST の顧客にはメール送信ボタンを出さないでほしい」

### domain 層がない世界
画面のコードに if 文を書き足す

API のコードにも if 文を書き足す

バッチ処理にも if 文を書き足す
→ どこに何を書いたか、そのうち誰も把握できなくなる
→ ルール変更のたびに「またどこか書き忘れてバグ…」が起きる

### domain 層がある世界
「Customer」や「Opportunity」のクラスが、
「この状態のときは〇〇してOK / ダメ」というルールを一ヶ所で持っている
画面やAPIからは、「この顧客に新規商談を作っていい？」
を domain に聞くだけ
→ ルールが変わっても domain だけ直せばよくなる。
　画面側・インフラ側は「その答えを使うだけ」になる。


### 2. 技術を変えやすくなる（DB や認証方式が変わっても、ビジネスの話はそのまま）

例：
- 最初は SQLite だけど、あとで Postgres ＋ RDS にしたい
- パスワード認証から、Cognito/LINEログインに変えたい

### domain 層がない世界
「顧客」「ユーザー」の概念が、SQL文やAPIの生データにベタベタにくっついている
DB を変えようとすると、ビジネスロジックとSQLが混ざった塊を全部書き換え
認証を変えようとすると、ビジネスルールとJWTロジックが混ざっているのでまとめて手術

### domain 層がある世界

domain は「顧客」「ユーザー」「トークン」などのビジネスの世界だけを持っている
DB や JWT の実装は、domain を満たすように裏で頑張る担当（infra）に閉じている
→ DB を変える・認証方式を変えるときは、
　infra 層を差し替えるだけで済む。
　「顧客とは何か」「ユーザーとは何か」の話は変えなくていい。

## application層
- 概要
  - アプリ内部での複雑な処理に必要なデータなども保有する
  - 入力（フィルタ条件、ページ情報、現在のユーザー）を受け取る
  - domain / repository を呼び出して必要な情報を集める
  - ビジネスルール・認可・ページング仕様を適用する
- application/配下の役割
  - read_models.pyなど
    - 「何を返すか」→ read_models.pyなど
    - 「このユースケースの結果は こういう形 で持ちたい」という データ定義
  - query_service.pyなど
    - 「どうやって返すか」→ services.py
    - 「その形のデータを どうやって作るか」という 処理（ユースケース）本体

- 結論
```
read_models.py
→ 「結果の形」を定義する（CustomerSummaryReadModel, CustomerListResult）

query_filter.py
→ 「入力条件の形」を定義する（CustomerFilter）

ports.py
→ 「インフラさん、こういう情報をください」という 要求の口（Port） を定義する
（CustomerQueryRepository）

query_service.py（読み取り系: GET）
→ それらを使って「顧客一覧ユースケースそのもの」を実装する
（CustomerQueryService.list_customers）

services.py（POST/PUT/DELETE/loginなど）
→ クラス名：AuthService, CustomerCommandService など
ログイン / パスワード変更 / ロール付け替え / ユーザー作成など
```

## infrastructure層
## interface層
- deps
  - FastAPI の Depends() で使う「依存解決関数」をまとめておく場所
  - 例:
    - DB セッションを作る get_db
    - ログインユーザーを取得する get_current_user
    - CustomerQueryService を組み立てて返す get_customer_query_service
  - 概要
    - routes（エンドポイント本体）に配線ロジックを書かないため
      - ルート側は「サービスをもらって呼ぶだけ」にしたい
    - 依存関係の作り方を一箇所で管理するため
      - DB を変えたい / キャッシュを挟みたいときに、この辺を触ればよい

- schemas
  - 「HTTP リクエスト / レスポンスの JSON の形」を定義する Pydantic モデル置き場
  - 例:
    - CustomerSummaryResponse
      - GET /customers の 1行分の JSON の形
    - CustomerListResponse
      - ページ付きの一覧レスポンス全体の形
  
  - 概要
    - 「フロントに見せる JSON の契約」をここで固定するため
    - application / domain のモデルと分離するため
      - application：CustomerSummaryReadModel（内部用）
      - interface：CustomerSummaryResponse（HTTP 用）
      - 双方の変更の影響を最低限にできる

- routes
  - 実際の HTTP エンドポイントを定義する「入り口本体」
    - 1. HTTP の情報を受け取る（パス、クエリ、ボディ）
    - 2. Depends で current_user や CustomerQueryService を受け取る
    - 3. CustomerQueryService.list_customers(...) など application 層を呼ぶ
    - 4. 返ってきた CustomerListResult を CustomerListResponse に詰め替えて返す

  - 概要
    - 「HTTP 世界」と「アプリ内部」をつなぐ翻訳役
    - DB は知らない
    - SQLAlchemy も知らない
    - やるのは「パラメータを受け取ってユースケース呼ぶ」「レスポンスに詰める」だけ

  - 流れ
  ```
  [ ブラウザ / フロント ]
         |
         v
  [ routes/customers.py ]  ← エンドポイント本体
    - Depends(get_customer_query_service)
    - response_model=CustomerListResponse
          |
          |  (Depends)
          v
  [ deps.py / deps.customer.py ] ← 依存解決係
    - get_db -> Session
    - get_customer_query_service -> CustomerQueryService
          |
          |  (コンストラクタ)
          v
  [ CustomerQueryService (application) ] ← ユースケース本体
    - customer_query_repo.fetch_customer_summaries(...)
          |
          |  (Port 経由)
          v
  [ SqlAlchemyCustomerQueryRepository (infrastructure) ] ← DB アクセス
  ```

## test
- 実行：python -m pytest 

## application/read_modelsとinfrastructure/schemaの使い分け

1. UI 向けの整形（flatten / ネスト変更）
  - application/customer/read_models.pyのように、すでに生成されている型の内容が必要なとき、継承すると依存関係が濃くなる。其為summary: XXX という形で一旦整形し、schemaの方でflat化させる

2. セキュリティ・情報マスキング
  - application 側の ReadModel は「業務的に全部持っている」
  - schema 側では絶対に出してはいけないものを落とす
  - 例えばパスワードや外部のアクセストークンなど

3. API バージョンやクライアント別の違い
  - application/read_models は変えたくない（内部ではずっと同じ構造で使いたい）
  - でも API は v1 / v2 でレスポンスを変えたい

4. ページング・メタ情報・リンクなどをくっつける
  - API レスポンスレベルで付けたい情報やフロントが楽になるメタ情報（has_next など）はinfra側で付けるなどできる

5. エラー表現・HTTP都合の構造
  - application: AuthenticationError, AuthorizationError, DomainValidationError など
  - schema: API として返すエラー JSON の形

## domain/modelのcreateメソッド
### 何を domain に寄せるべきかの判断軸
- 「これ、domain に追加すべき？」と迷ったときの基準はだいたい次の 2 つです。
  - DB や外部サービスを見なくても判断できるか？
    - Yes → domain に寄せてよい候補
    - No → application / infra の責務

- このルールは「Customer という概念」に一生ついて回りそうか？
  - 例えば： 顧客の名前が空は絶対 NG → domain
  - 顧客を新規作成した瞬間は ACTIVE 扱いにしたい → domain
  - ある画面だけで一時的に有効なフィルタ条件 → application / UI 側