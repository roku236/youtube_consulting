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
  <title>SAMUNE STYLE | YouTubeサムネイルギャラリー</title>
  <meta name="description" content="良質なYouTubeサムネイルデザインを集めたギャラリーサイト。ジャンルやカラーで絞り込んで参考にできます。" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>

  <header class="g-header">
    <div class="g-header__inner">
      <a href="#" class="g-logo">
        <span class="g-logo__icon">▶</span>
        <span>THUMB GALLERY</span>
      </a>
      <p class="g-header__tagline">良質なサムネイルデザインを集めたギャラリー</p>
    </div>
  </header>

  <main class="g-main">
    <section class="g-filterbar">
      <div class="g-filterbar__group">
        <span class="g-filterbar__label">ジャンル</span>
        <div class="g-chips" id="genreChips"></div>
      </div>
      <div class="g-filterbar__group">
        <span class="g-filterbar__label">カラー</span>
        <div class="g-chips g-chips--color" id="colorChips"></div>
      </div>
      <div class="g-filterbar__group g-filterbar__group--right">
        <button class="g-reset" id="resetFilters" type="button">リセット</button>
        <span class="g-count" id="resultCount"></span>
      </div>
    </section>

    <section class="g-grid" id="thumbGrid"></section>

    <p class="g-empty" id="emptyState" hidden>条件に合うサムネイルが見つかりませんでした。</p>
  </main>

  <footer class="g-footer">
    <p>© 2026 THUMB GALLERY — サムネイルデザインの参考サイト</p>
    <p><a href="../admin/">管理画面</a></p>
  </footer>

  <script>
    const THUMBNAILS = <?php echo json_encode($thumbnails, JSON_UNESCAPED_UNICODE); ?>;
  </script>
  <script src="script.js"></script>
</body>
</html>
