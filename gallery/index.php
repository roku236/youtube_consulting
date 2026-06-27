<?php
require_once __DIR__ . '/db.php';

$pdo = get_db();
$thumbnails = $pdo->query('SELECT * FROM thumbnails ORDER BY id DESC')->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>THUMB GALLERY | YouTubeサムネイルギャラリー</title>
  <meta name="description" content="良質なYouTubeサムネイルデザインを集めたギャラリーサイト。ジャンルやカラーで絞り込んで参考にできます。" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Cormorant+Garamond:ital@1&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>

  <div class="g-layout">

    <aside class="g-sidebar">
      <a href="#" class="g-logo">
        <span class="g-logo__main">THUMB GALLERY</span>
        <span class="g-logo__sub">Thumbnail Design Gallery</span>
      </a>

      <nav class="g-sidebar__nav">
        <h2 class="g-sidebar__heading">CATEGORY</h2>
        <ul class="g-sidebar__list" id="genreList"></ul>
      </nav>

      <div class="g-sidebar__nav">
        <h2 class="g-sidebar__heading">COLOR</h2>
        <ul class="g-sidebar__list g-sidebar__list--color" id="colorList"></ul>
      </div>
    </aside>

    <main class="g-main">
      <p class="g-tagline">目を惹かれる良質なデザインのサムネイルを集めたギャラリーサイト</p>
      <div class="g-toolbar">
        <button class="g-reset" id="resetFilters" type="button">絞り込みをリセット</button>
        <span class="g-count" id="resultCount"></span>
      </div>

      <section class="g-grid" id="thumbGrid"></section>

      <p class="g-empty" id="emptyState" hidden>条件に合うサムネイルが見つかりませんでした。</p>

      <footer class="g-footer">
        <p>© 2026 THUMB GALLERY — サムネイルデザインの参考サイト</p>
        <p><a href="../admin/">管理画面</a></p>
      </footer>
    </main>

  </div>

  <script>
    const THUMBNAILS = <?php echo json_encode($thumbnails, JSON_UNESCAPED_UNICODE); ?>;
  </script>
  <script src="script.js"></script>
</body>
</html>
