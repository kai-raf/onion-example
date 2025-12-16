
## 実務での進め方（例：auth）

### 実務でまず降ってくる“要件”イメージ
例えば今回の認証なら、PM やリーダーから降ってくるのは、ざっくりこんなレベルです：
- 「メール + パスワードでログインしたい」
- 「フロントからは JWT で認証したい」
- 「ログイン中ユーザーの情報を /me で取れるようにしたい」
- 「既存の /customers はログイン必須にしたい」

### 頭の中の“思考の順番”イメージ

**前提**
Userなどdomain/modelについてPMと会話しざっくり最低限のmodel.pyを作っておく
  - このシステムにとっての User とは？
  - どんな状態を持つか？
  - どんな振る舞いがあるか？（ログインできる・できない、どのロールを持ってるか etc）

**Step 0: ユースケースを一言にする**
  - 「ログインする」
  - 「トークンからユーザーを取り出す」
  - 「ログイン中ユーザーのプロフィールを見る」

-> じゃあ 「認証まわりのユースケースをまとめるサービス」 が 1 個欲しいな
-> 名前は… AuthService でいいか

ここで初めて
```python
class AuthService:
    ...

```
という箱のイメージが浮かぶ

**Step 1: AuthService のメソッドだけ先に決める**
まずは中身は書かずに「こういうメソッドがあったら嬉しいよね」を決めます。

- ログイン → authenticate(email, password) -> User
- トークン発行 → create_access_token(user) -> AuthToken
- /me → get_user_from_token(token) -> User と build_current_user_read_model(user) -> CurrentUserReadModel

なので、最初は services.py に メソッドシグネチャだけ 置くことが多いです。
```python
class AuthService:
    def authenticate(self, email: str, password: str) -> User: ...
    def create_access_token(self, user: User) -> AuthToken: ...
    def get_user_from_token(self, token: str) -> User: ...
    def build_current_user_read_model(self, user: User) -> CurrentUserReadModel: ...

```

**Step 2: 「この中で何が必要になるか？」から ports を逆算する**
次にAuthService.authenticateの中身をシミュレーションする

- email から user を探したい → UserRepository.get_by_email(email)
- password を検証したい → PasswordHasher.verify(plain, hashed)
- JWT を発行したい → TokenProvider.encode(payload, expires_in)
ここで初めて UserRepository / PasswordHasher / TokenProvider みたいな 依存物が必要なことを確認

→ じゃあ ports.py にインターフェースを切っておこう、となる。

つまり現実は：

1. 先に AuthService のメソッドだけ考える
2. その実装案を頭の中でシミュレーションする
3. 「あ、外部の力借りないと無理だな」と思ったタイミングで port を生やす

という**“中身を妄想 → 依存が見える → port を掘る”**の順番が多いです。

**Step 3: ReadModel が必要かどうかは「APIの形」を見て決める**
次に /me のレスポンス仕様を見ます。

- API 仕様：「id, email, full_name, roles, is_superuser を返したい」
- domain User を見る：「name_sei, name_mei, roles: List[Role] みたいな構造だな」

ここで考えるのは：
```
「domain の User そのまま返すと、API でいらない情報も混ざるし、構造も違うな」
「roles を文字列に変換したいし、full_name も組み立てたい」
「じゃあ application 層に /me 専用の ReadModel を作ろう」
```
なので read_models.py は、最初から決め打ちで作るというより
「API のレスポンス仕様」を見て「domain そのままでは辛い」となったタイミングで切り出すことが多いです。

**Step 4: ドメインモデルは「最低限必要な情報」が見えたところから**
「domain 層の主役」として先に存在していることが多いです。ex: User
AuthTokenのように実際の実装にあたって必要になったものは、このStep4で随時追加していけばOK

**Step 5: serviceの肉付け**
infrastructureやinterfaceの実装に入る前に、ports.py（application 層が定義する “依存の抽象”（＝infrastructure が「実装させてもらう契約」））を考慮し、serviceの実際のユースケースの流れ（認証ロジック、トークン検証など）を書いていく

**Step 6: infrastructure層の実装**
SqlAlchemyUserRepository で UserRepository ポートを満たす
Argon2PasswordHasher で PasswordHasher ポートを満たす
JwtTokenProvider で TokenProvider ポートを満たす

ここで初めて
```
SQLAlchemy
pwdlib[argon2]
PyJWT
settings（.env）
```

などの具体的な技術が登場します。


**Step 7: interface層の実装**

- schemas/auth.py に Pydantic の I/O 型（LoginRequest, TokenResponse, CurrentUserResponse）を定義

- deps/auth.py で
  - infra 実装を組み立て
  - AuthService に注入し
  - get_auth_service, get_current_user を FastAPI の Depends に乗せる

- routes/auth.py で
  - /api/auth/login
  - /api/auth/me

- 既存の /api/customers に current_user: User = Depends(get_current_user) を追加して認証必須化

**Step 8: 全体への組み込み・既存エンドポイントへの適用**
- router/main.py / ルート登録に新しい router を組み込む
  - app.include_router(auth_router, prefix="/api/auth")
- 既存エンドポイントに認証を適用
  - /api/customers にcurrent_user: User = Depends(get_current_user) を追加
  - CustomerQueryService の引数に current_user を渡す形に変更
- ロールベース認可の「入り口」も決めておく
  - 例えば require_role("ADMIN") 的なデコレータや Depends をどこに置くかの設計だけ先にしておく

**Step 9:　テストを書く（レイヤーごとに）**
- application 層のテスト（AuthService 単体）
- infrastructure 層のテスト
- interface 層のテスト

**Step 9:　エラーハンドリング・セキュリティまわりの磨き込み**
- 401 / 403 の挙動の統一
  - 401 のレスポンスヘッダ WWW-Authenticate: Bearer を必ず付ける
  - 認可 NG（ロール足りない）は 403 にしてメッセージを分ける
- 例外ハンドラ
  - AuthenticationError / TokenError を FastAPI の exception_handler で HTTP エラーにマッピングするか検討
- セキュリティチェック


## 抽象的な思考順序まとめ
1. ユースケースを一言にする
  - 「ログイン」「トークンからユーザーを特定」「/me を返す」

2. ユースケース単位で“サービスクラス”を決める
  - 「認証に関するユースケースをまとめる箱 → AuthService」

3. サービスのメソッドだけ先に決める
  - authenticate, create_access_token, get_user_from_token, build_current_user_read_model

4. メソッドの中身を“頭の中で実装”してみる
  - ここで「UserRepository / PasswordHasher / TokenProvider が必要だな」と気づく

5. 必要になった瞬間に ports を切る
  - 「infra で実装してもらうための“依存の穴”」として Protocol を定義

6. API 仕様と domain のギャップを見て ReadModel を作るか判断
  - domain そのまま返すと辛いときだけ application/read_models を追加

7. 順番に縦の1本を通す
  - まず /auth/login の happy path を通す
  - 次に /auth/me
  - そのあとエラーハンドリングやテストを固める