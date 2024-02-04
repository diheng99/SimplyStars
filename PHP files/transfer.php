// transfer.php
<?php
function httpRequest($url, $post="") {
    global $settings;

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);

    $headers = array('Content-Type: application/json');
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

    if (!empty($post)) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
    }

    $response = curl_exec($ch);
    if (!$response) {
        throw new Exception("Error getting data from server ($url): " . curl_error($ch));
    }

    curl_close($ch);
    return $response;
}

try {
    $data = [
        'course_code' => $course_code,
        'user_id' => $user_id,
        'html_content' => $htmlContent
    ];

    $response = httpRequest('http://127.0.0.1:5000/add_course_schedule', json_encode($data));

    echo "Data transferred successfully";

} catch (Exception $e) {
    die($e->getMessage());
}
