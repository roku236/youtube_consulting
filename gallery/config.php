<?php
// 本番（お名前.comのレンタルサーバー）にアップロードする前に、以下を書き換えてください。
//
// 1. お名前.comの「データベース設定」画面で、MySQLデータベースを1つ作成する
// 2. そこで発行される「ホスト名・データベース名・ユーザー名・パスワード」を下に入力する
// 3. ADMIN_PASSWORD を、管理画面用の好きなパスワードに変更する

define('DB_DRIVER', 'mysql'); // 本番は 'mysql' のまま。ローカル確認用に 'sqlite' にも切り替え可能。

define('DB_HOST', 'localhost');
define('DB_NAME', 'your_database_name');
define('DB_USER', 'your_database_user');
define('DB_PASS', 'your_database_password');

// SQLiteで動作確認したい場合のファイル保存先（DB_DRIVERが'sqlite'の時のみ使用）
define('SQLITE_PATH', __DIR__ . '/data.sqlite');

// 管理画面のログインパスワード（必ず変更してください）
define('ADMIN_PASSWORD', 'change-this-password');

session_start();
