<?php
require_once __DIR__ . '/../gallery/config.php';

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (hash_equals(ADMIN_PASSWORD, (string) ($_POST['password'] ?? ''))) {
        $_SESSION['admin_logged_in'] = true;
        header('Location: index.php');
        exit;
    }
    $error = 'パスワードが正しくありません。';
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>管理画面ログイン | THUMB GALLERY</title>
  <link rel="stylesheet" href="admin.css" />
</head>
<body class="a-login-body">
  <form class="a-login-card" method="post">
    <h1>管理画面ログイン</h1>
    <?php if ($error): ?><p class="a-error"><?php echo htmlspecialchars($error); ?></p><?php endif; ?>
    <label for="password">パスワード</label>
    <input type="password" id="password" name="password" required autofocus />
    <button type="submit">ログイン</button>
  </form>
</body>
</html>
