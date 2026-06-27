<?php
require_once __DIR__ . '/config.php';

function get_db(): PDO {
    static $pdo = null;
    if ($pdo !== null) {
        return $pdo;
    }

    if (DB_DRIVER === 'sqlite') {
        $pdo = new PDO('sqlite:' . SQLITE_PATH);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS thumbnails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                channel TEXT NOT NULL,
                genre TEXT NOT NULL,
                color TEXT NOT NULL,
                views TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ");
    } else {
        $dsn = sprintf('mysql:host=%s;dbname=%s;charset=utf8mb4', DB_HOST, DB_NAME);
        $pdo = new PDO($dsn, DB_USER, DB_PASS);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS thumbnails (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                channel VARCHAR(255) NOT NULL,
                genre VARCHAR(100) NOT NULL,
                color VARCHAR(50) NOT NULL,
                views VARCHAR(50) NOT NULL,
                url VARCHAR(500) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
    }

    $count = (int) $pdo->query('SELECT COUNT(*) FROM thumbnails')->fetchColumn();
    if ($count === 0) {
        seed_thumbnails($pdo);
    }

    return $pdo;
}

function seed_thumbnails(PDO $pdo): void {
    $seed = [
        ["1ヶ月で-10kg!?\n本当にヤバいダイエット", "FitLife Japan", "美容・健康", "pink", "182万", "https://www.youtube.com/"],
        ["新NISA、結局どうすればいいの?", "マネーの学校", "ビジネス", "blue", "98万", "https://www.youtube.com/"],
        ["最強装備で挑む裏ボス戦", "ゲーム実況ちゃんねる", "ゲーム", "purple", "320万", "https://www.youtube.com/"],
        ["誰でも作れる絶品パスタ3選", "おうちごはん研究所", "料理", "orange", "75万", "https://www.youtube.com/"],
        ["朝5時に起きたら人生変わった", "ミニマル生活", "Vlog", "yellow", "54万", "https://www.youtube.com/"],
        ["プログラミング独学、3ヶ月の記録", "Code Diary", "教育", "green", "41万", "https://www.youtube.com/"],
        ["新作スマホを徹底レビュー", "ガジェット部", "ガジェット", "black", "210万", "https://www.youtube.com/"],
        ["深夜のテンションで雑談", "深夜ラジオ部屋", "エンタメ", "red", "63万", "https://www.youtube.com/"],
    ];
    $stmt = $pdo->prepare('INSERT INTO thumbnails (title, channel, genre, color, views, url) VALUES (?, ?, ?, ?, ?, ?)');
    foreach ($seed as $row) {
        $stmt->execute($row);
    }
}
