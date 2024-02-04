<?php
set_time_limit(60);
$settings['cookiefile'] = "cookies.tmp";

function httpsRequest($url, $post="") {
    global $settings;

    $ch = curl_init();
    //Change the user agent below suitably
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0');
    curl_setopt($ch, CURLOPT_URL, ($url));
    curl_setopt( $ch, CURLOPT_ENCODING, "UTF-8" );
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt ($ch, CURLOPT_COOKIEFILE, $settings['cookiefile']);
    curl_setopt ($ch, CURLOPT_COOKIEJAR, $settings['cookiefile']);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);

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
    ### Course data
    $course_code = filter_input(INPUT_POST, 'course_code', FILTER_SANITIZE_STRING);
    $user_id = filter_input(INPUT_POST, 'user_id', FILTER_SANITIZE_STRING);

    # $request is an associative array
    $request['r_search_type'] = 'F';
    $request['boption'] = 'Search';
    $request['acadsem'] = '2023;2';
    $request['r_subj_code'] = $course_code;
    $request['staff_access'] = 'false';

    $response = httpsRequest("https://wish.wis.ntu.edu.sg/webexe/owa/AUS_SCHEDULE.main_display1", $request);
    $htmlContent = $response;
    include('transfer.php');

    echo "OK";
} catch (Exception $e) {
    die ($e->getMessage());
}