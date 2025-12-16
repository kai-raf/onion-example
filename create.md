## 全体のメンタルモデルまとめ
最後に、頭の中のイメージを一枚の絵にするとこんな感じです。

**add**
「このオブジェクトを DB に反映対象として管理する」と Session に登録する
まだ SQL は実行されない（ステージングに載せるイメージ）

**flush**
「ステージングされている変更を、今のトランザクションで実際に DB へ送る」
INSERT/UPDATE/DELETE の SQL が発行され、DB に書き込まれる
ただし トランザクションはまだ開いたまま → rollback すればなかったことにできる
PK の採番もここで行われる（AUTO_INCREMENT）

**refresh**
「DB 側に書き込まれた行を SELECT して、ORM に最新値を反映」
default 値 / trigger / version / timestamp など、「DB が決めた値」を ORM に戻す
「DB に確定しているその行の内容で、ORM インスタンスを“上書き同期”する」
つまりDBのdefaultでcreated_atやversionが決められる時、refreshしないとPython側のORMにはcreated_at等が反映されていない
その反映を行う

**commit（FastAPI の get_db などで実行）**
そのリクエスト内のトランザクションを確定
ここで初めて「他の接続からも新しい行が見える」状態になる
ここまでに行った INSERT/UPDATE/DELETE は rollback できなくなる

## 時系列
①リクエスト受付
②FastAPI が Depends(get_db) を解決するために get_db() を呼ぶ
  - db = SessionLocal() で Session 作成
  - yield db でいったん中断し、「db を引数に持った状態」で path function（router）が呼ばれる
③path function 内（＝あなたの routes → service → repository の処理）
  - self._session.add(orm)
  - self._session.flush()
  - self._session.refresh(orm)
  - …その他の処理
  - 正常にリターンし、レスポンスオブジェクト（Pydantic モデルなど）を返す
④path function が終わると、FastAPI は依存関数の残り（yield の後）を実行
  - db.commit() が呼ばれる ← ここがトランザクション確定
⑤commit に成功したらレスポンスがクライアントへ送られる
⑥finally で db.close() 実行