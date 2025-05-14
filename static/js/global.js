jQuery(document).ready(function($) {
    $('[data-toggle]').on('click', function() {
        // クリックされたボタンのdata-toggle属性の値を取得
        var target = $(this).data('toggle');

        // 対応するdata-content属性の値が一致する要素をスライドで開閉
        $('[data-content="' + target + '"]').slideToggle(300);
        $(this).toggleClass('active');
    });
});


jQuery(document).ready(function($) {
    // ドロワーの初期化
    $('.drawer').drawer();

    // ナビゲーション内のリンクがクリックされたときにドロワーを閉じる
    $('.drawer-menu a').on('click', function() {
        $('.drawer').drawer('close');
    });
});