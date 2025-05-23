// $(document).ready(function() {
//     // midashiの位置を取得
//     var blockPosition = $('.index #midashi').offset().top; // #midashi の位置を取得
//     var isVisible = false; // 現在の表示状態を保持するフラグ

//     $(window).on('scroll', function() {
//         var scrollTop = $(this).scrollTop(); // 現在のスクロール位置を取得
//         if (scrollTop > blockPosition && !isVisible) {
//             $('#navigation').addClass('visible'); // visibleクラスを付与
//             isVisible = true;
//         } else if (scrollTop <= blockPosition && isVisible) {
//             $('#navigation').removeClass('visible'); // visibleクラスを削除
//             setTimeout(() => $('#navigation').css('visibility', 'hidden'), 500); // visibilityをhiddenに
//             isVisible = false;
//         }
//     });
// });

  
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
  /* ===== 初期表示 ===== */
  $("#male").hide();
  $("#female").show();
  $(".button-area button[data-toggle='female']").addClass("active"); // 初期active

  /* ===== クリック ===== */
  $(".button-area button").on("click", function () {
    const targetId = $(this).data("toggle");

    // 表示切り替え
    $(".oaite__loop").hide();
    $("#" + targetId).fadeIn();

    // active切り替え
    $(".button-area button").removeClass("active");
    $(this).addClass("active");
  });
});


  $(document).ready(function(){
    $('.slider').slick({
      infinite: true,
      slidesToShow: 1,
      slidesToScroll: 1,
      autoplay: true,
      autoplaySpeed: 0,
      speed: 6000,
      cssEase: 'linear',
      variableWidth: true
    });
  });


const currentPage = window.location.pathname.split("/").pop().replace(".html", ""); 
document.querySelectorAll('.nav__wrap .menu ul li a').forEach(link => {
    if (link.classList.contains(currentPage)) { 
        link.classList.add('current');
    }
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




