<?php
require_once __DIR__ . '/../gallery/config.php';
session_destroy();
header('Location: login.php');
exit;
