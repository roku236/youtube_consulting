<?php
require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/../gallery/db.php';

$pdo = get_db();
$message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'delete') {
    $stmt = $pdo->prepare('DELETE FROM thumbnails WHERE id = ?');
    $stmt->execute([(int) $_POST['id']]);
    $message = '削除しました。';
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'add') {
    $stmt = $pdo->prepare('INSERT INTO thumbnails (title, channel, genre, color, views, url) VALUES (?, ?, ?, ?, ?, ?)');
    $stmt->execute([
        trim($_POST['title'] ?? ''),
        trim($_POST['channel'] ?? ''),
        trim($_POST['genre'] ?? ''),
        $_POST['color'] ?? 'red',
        trim($_POST['views'] ?? ''),
        trim($_POST['url'] ?? ''),
    ]);
    $message = '追加しました。';
}

$thumbnails = $pdo->query('SELECT * FROM thumbnails ORDER BY id DESC')->fetchAll(PDO::FETCH_ASSOC);

$colors = [
    'red' => 'レッド', 'blue' => 'ブルー', 'yellow' => 'イエロー', 'green' => 'グリーン',
    'purple' => 'パープル', 'pink' => 'ピンク', 'orange' => 'オレンジ', 'black' => 'ブラック',
];
?>
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>管理画面 | THUMB GALLERY</title>
  <link rel="stylesheet" href="admin.css" />
</head>
<body>
  <header class="a-header">
    <h1>THUMB GALLERY 管理画面</h1>
    <div class="a-header__actions">
      <a href="../gallery/" target="_blank">公開サイトを見る</a>
      <a href="logout.php">ログアウト</a>
    </div>
  </header>

  <main class="a-main">
    <?php if ($message): ?><p class="a-message"><?php echo htmlspecialchars($message); ?></p><?php endif; ?>

    <section class="a-card">
      <h2>新しいサムネイルを追加</h2>
      <form method="post" class="a-form">
        <input type="hidden" name="action" value="add" />
        <div class="a-form__row">
          <label>タイトル
            <textarea name="title" required placeholder="動画タイトル"></textarea>
          </label>
          <label>チャンネル名
            <input type="text" name="channel" required placeholder="チャンネル名" />
          </label>
        </div>
        <div class="a-form__row">
          <label>ジャンル
            <input type="text" name="genre" required placeholder="例: ビジネス" />
          </label>
          <label>カラー
            <select name="color">
              <?php foreach ($colors as $key => $label): ?>
                <option value="<?php echo $key; ?>"><?php echo $label; ?></option>
              <?php endforeach; ?>
            </select>
          </label>
          <label>再生回数
            <input type="text" name="views" placeholder="例: 100万" />
          </label>
        </div>
        <label>YouTube URL
          <input type="url" name="url" required placeholder="https://www.youtube.com/watch?v=..." />
        </label>
        <button type="submit">追加する</button>
      </form>
    </section>

    <section class="a-card">
      <h2>登録済み一覧（<?php echo count($thumbnails); ?>件）</h2>
      <table class="a-table">
        <thead>
          <tr>
            <th>サムネ</th><th>タイトル</th><th>チャンネル</th><th>ジャンル</th><th>カラー</th><th>再生回数</th><th></th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($thumbnails as $t): ?>
            <tr>
              <td><span class="a-swatch bg-<?php echo htmlspecialchars($t['color']); ?>"></span></td>
              <td><?php echo nl2br(htmlspecialchars($t['title'])); ?></td>
              <td><?php echo htmlspecialchars($t['channel']); ?></td>
              <td><?php echo htmlspecialchars($t['genre']); ?></td>
              <td><?php echo htmlspecialchars($colors[$t['color']] ?? $t['color']); ?></td>
              <td><?php echo htmlspecialchars($t['views']); ?></td>
              <td>
                <a href="edit.php?id=<?php echo $t['id']; ?>">編集</a>
                <form method="post" style="display:inline" onsubmit="return confirm('削除しますか？');">
                  <input type="hidden" name="action" value="delete" />
                  <input type="hidden" name="id" value="<?php echo $t['id']; ?>" />
                  <button type="submit" class="a-link-btn">削除</button>
                </form>
              </td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
