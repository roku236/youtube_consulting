<?php
require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/../gallery/db.php';

$pdo = get_db();
$id = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);

$stmt = $pdo->prepare('SELECT * FROM thumbnails WHERE id = ?');
$stmt->execute([$id]);
$thumb = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$thumb) {
    header('Location: index.php');
    exit;
}

$message = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $stmt = $pdo->prepare('UPDATE thumbnails SET title = ?, channel = ?, genre = ?, color = ?, views = ?, url = ? WHERE id = ?');
    $stmt->execute([
        trim($_POST['title'] ?? ''),
        trim($_POST['channel'] ?? ''),
        trim($_POST['genre'] ?? ''),
        $_POST['color'] ?? 'red',
        trim($_POST['views'] ?? ''),
        trim($_POST['url'] ?? ''),
        $id,
    ]);
    header('Location: index.php');
    exit;
}

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
  <title>編集 | THUMB GALLERY 管理画面</title>
  <link rel="stylesheet" href="admin.css" />
</head>
<body>
  <header class="a-header">
    <h1>サムネイルを編集</h1>
    <div class="a-header__actions">
      <a href="index.php">一覧に戻る</a>
    </div>
  </header>

  <main class="a-main">
    <section class="a-card">
      <form method="post" class="a-form">
        <input type="hidden" name="id" value="<?php echo $thumb['id']; ?>" />
        <div class="a-form__row">
          <label>タイトル
            <textarea name="title" required><?php echo htmlspecialchars($thumb['title']); ?></textarea>
          </label>
          <label>チャンネル名
            <input type="text" name="channel" required value="<?php echo htmlspecialchars($thumb['channel']); ?>" />
          </label>
        </div>
        <div class="a-form__row">
          <label>ジャンル
            <input type="text" name="genre" required value="<?php echo htmlspecialchars($thumb['genre']); ?>" />
          </label>
          <label>カラー
            <select name="color">
              <?php foreach ($colors as $key => $label): ?>
                <option value="<?php echo $key; ?>" <?php echo $key === $thumb['color'] ? 'selected' : ''; ?>><?php echo $label; ?></option>
              <?php endforeach; ?>
            </select>
          </label>
          <label>再生回数
            <input type="text" name="views" value="<?php echo htmlspecialchars($thumb['views']); ?>" />
          </label>
        </div>
        <label>YouTube URL
          <input type="url" name="url" required value="<?php echo htmlspecialchars($thumb['url']); ?>" />
        </label>
        <button type="submit">保存する</button>
      </form>
    </section>
  </main>
</body>
</html>
