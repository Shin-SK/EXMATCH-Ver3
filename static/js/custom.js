// custom.js
  
$(document).ready(function () {
    $("[data-toggle='click']").on("click", function () {
        const wrap = $(this).closest(".box, .click__wrap"); // 親のwrapを取得
        const target = wrap.find("#contents"); // ターゲットの#contentsを取得

        // 表示・非表示を切り替え
        if (target.is(":hidden")) {
            target.slideDown(); // ふわっと表示
            $(this).addClass("active"); // 回転クラスを追加
        } else {
            target.slideUp(); // ふわっと非表示
            $(this).removeClass("active"); // 回転クラスを削除
        }
    });
});


$(function () {
  $('#female .slider').slick({
    infinite:true, slidesToShow:1, variableWidth:true,
    autoplay:true, autoplaySpeed:0, speed:6000, cssEase:'linear'
  });

  $("#male").hide();
  $("#female").show();
  $(".button-area button[data-toggle='female']").addClass("active");

  $(".button-area button").on("click", function () {
    const id = $(this).data("toggle");
    const $loop   = $("#"+id).show();      // 先に表示
    const $slider = $loop.find(".slider");

    // まだなら生成
    if ( ! $slider.hasClass("slick-initialized") ){
      $slider.slick({
        infinite:true, slidesToShow:1, variableWidth:true,
        autoplay:true, autoplaySpeed:0, speed:6000, cssEase:'linear'
      });
    }

    // 毎回 幅を再計算  ← ★これを追加
    $slider.slick("setPosition");

    $(".oaite__loop").not($loop).hide();
    $(".button-area button").removeClass("active");
    $(this).addClass("active");
  });

});



  $(document).ready(function(){
    $('.slide-area__wrap').slick({
      dots: true,          // 下部インジケータ
      arrows: false,       // 矢印不要なら
      infinite: true,
      speed: 300,
      slidesToShow: 1,
      slidesToScroll: 1,
      swipe: true,        // スワイプ操作を許可
      touchMove: true,    // フリックで移動
      draggable: true,    // PC でドラッグ移動
      swipeToSlide: true  // 途中からでも次スライドへ
    });
  });

const currentPage = window.location.pathname.split("/").pop().replace(".html", ""); 
document.querySelectorAll('.nav__wrap .menu ul li a').forEach(link => {
    if (link.classList.contains(currentPage)) { 
        link.classList.add('current');
    }
});


// mmenu-light 初期化（1メニューだけならこれで OK）
document.addEventListener('DOMContentLoaded', () => {
  const mm   = new MmenuLight(document.getElementById('menu-main'), 'all');
  mm.navigation();
  const drawer = mm.offcanvas();

  document.getElementById('toggle-main')
          .addEventListener('click', e => { e.preventDefault(); drawer.open(); });
});


/* ================== JS：mainが頭から離れたら表示 ================== */
$(function () {
  const $cv = $('#cv');
  const mainTop = $('#home').offset().top; // main がドキュメント内で始まる位置

  $(window).on('scroll resize', function () {
    const scrolledPast = $(this).scrollTop() > mainTop; // 0より大きければ main は画面外
    $cv.toggleClass('show', scrolledPast);              // true で add, false で remove
  }).trigger('scroll'); // リロード直後の状態も反映
});


//ファイル選択のプレビュー表示
function setupPreview(inputId, previewId, clearButtonId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const clearButton = document.getElementById(clearButtonId);

    input.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="プレビュー画像" style="max-width: 100%; height: auto;">`;
            };
            reader.readAsDataURL(file);
        }
    });

    clearButton.addEventListener('click', function() {
        input.value = '';
        preview.innerHTML = '';
    });
}

setupPreview('formGroupLCIQDiagnosis', 'previewLCIQ', 'clearButtonLCIQ');
setupPreview('formGroupFacePhoto', 'previewFace', 'clearButtonFace');
setupPreview('formGroupPhoto1', 'previewPhoto1', 'clearButtonPhoto1');
setupPreview('formGroupPhoto2', 'previewPhoto2', 'clearButtonPhoto2');
setupPreview('formGroupPhoto3', 'previewPhoto3', 'clearButtonPhoto3');





