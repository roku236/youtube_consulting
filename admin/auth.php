<?php
require_once __DIR__ . '/../gallery/config.php';

if (empty($_SESSION['admin_logged_in'])) {
    header('Location: login.php');
    exit;
}
