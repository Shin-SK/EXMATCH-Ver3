<!-- src/views/H2Lciq.vue -->
<script setup>
import { onMounted } from 'vue'
onMounted(() => { document.title = 'LCIQスコアはどうやってはかるの？' })
</script>

<template>
  <section class="h2lciq">
    <div class="head-set">
      <h2>LCIQ</h2>
      <h3>価値観診断</h3>
    </div>
    <div class="head text-center mb-5">
      <span class="ja d-block fw-bold fs-1">LCIQスコアのはかりかた</span>
      <span class="en">How to measure the score of LCIQ</span>
    </div>

    <div class="wrap wrap-1 text-center mb-5">
      <div class="main-title h5 mb-3">まずはここにアクセス</div>
      <a
        href="https://lciq-diagnosis.com/home?agent_id=0672689"
        target="_blank" rel="noopener"
        class="btn btn-warning w-100 mb-3"
      >LCIQ診断</a>
      <p>こちらはLCIQをはかる専用ページです！<br>楽しんで、いってらっしゃい！</p>
    </div>

    <div class="wrap wrap-2 mb-2">
      <div class="main-title h5 text-center mb-3">LCIQとは？</div>
      <p class="text-center mb-2">６つの恋愛力を分析し、<br>あなたの恋愛偏差値をスコアリング！</p>

      <div class="point point-1 row g-4 align-items-center mb-4">
        <div class="col-md-6">
          <div class="ratio ratio-4x3 bg-light rounded overflow-hidden">
            <img src="/img/honki-1.webp" alt="" class="img-fluid object-fit-cover">
          </div>
        </div>
        <div class="col-md-6">
          <div class="title fw-bold mb-2">恋愛に関連する６つの恋愛力でスコアリングをグラフ化</div>
          <p>表現力、楽転力、認識力、共感力、魅了力、継続力。<br>
             この６つの力は、潜在的な環境や意識に加え、日常の仕事や趣味の環境や対人感覚、さらにはその時の精神状態によってスコアリングされます。</p>
        </div>
      </div>

      <div class="point point-2 row g-4 align-items-center flex-md-row-reverse">
        <div class="col-md-6">
          <div class="title fw-bold mb-2">総合点を出し、それぞれの力の特徴や対策なども明確に。</div>
          <p>LCIQ®診断は資格制度のある恋愛教育システムなので、ただ結果を見るだけでなく、その先の心構えや日々の行動アドバイスもおこなっています。</p>
        </div>
        <div class="col-md-6">
          <div class="ratio ratio-4x3 bg-light rounded overflow-hidden">
            <img src="/img/honki-4.webp" alt="" class="img-fluid object-fit-cover">
          </div>
        </div>
      </div>
    </div>

    <div class="wrap wrap-3 mb-5 text-center">
      <div class="main-title h5 mb-2 mt-5">登録方法</div>
      <p class="mb-3 text-center">まずは公式サイトで診断を受ける</p>
      <a
        href="https://lciq-diagnosis.com/home?agent_id=0672689"
        target="_blank" rel="noopener"
        class="btn btn-warning w-100 my-5"
      >LCIQ診断</a>
		<div class="area">
		<div class="hscroll">
			<div class="d-flex flex-nowrap align-items-center gap-3 py-2">
			<img src="/img/h2LCIQ_1.png" alt="" class="guide-shot flex-shrink-0">
			<img src="/img/arrow.svg"     alt="" class="arrow      flex-shrink-0">
			<img src="/img/h2LCIQ_2.png" alt="" class="guide-shot flex-shrink-0">
			<img src="/img/arrow.svg"     alt="" class="arrow      flex-shrink-0">
			<img src="/img/h2LCIQ_3.png" alt="" class="guide-shot flex-shrink-0">
			</div>
		</div>
		</div>
    </div>
    
    <div class="wrap wrap-4 mb-5 text-center">
      <div class="main-title h5 mb-3">ここをスクショ</div>
      <div class="ratio ratio-16x9 bg-light rounded overflow-hidden mb-2">
        <img src="/img/h2LCIQ_4.png" alt="" class="img-fluid object-fit-contain">
      </div>
      <div class="underline fw-bold my-5">点数が低くても大丈夫！</div>
      <p>LCIQ®診断の恋愛スコアは、少しの意識で上げていくことができます！６つの力で恋愛力をアップさせ、自分も周りも幸せになれるチャンスです！</p>
    </div>

    <div class="wrap text-center mb-5">
      <div class="main-title h5">プロフィール編集で入力しよう</div>
      <router-link :to="{ name:'profile-edit' }" class="btn btn-primary my-5 w-100">プロフィール編集</router-link>
    </div>

    <div class="wrap wrap-last text-center text-muted pb-4">
      出会いは。すぐそこに。
    </div>
  </section>
</template>

<style scoped>
.head .en{ font-size:2rem }
.btn-lciq{ min-width:220px }
.guide-shot{ max-width:260px; width:100%; height:auto; border-radius:12px; background:#f8f9fa }
.arrow{ width:32px; opacity:.6 }
.underline{ text-decoration:underline; text-underline-offset:2px }
.object-fit-cover{ object-fit:cover }
.object-fit-contain{ object-fit:contain }
.hscroll{
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x proximity;   /* 任意：スナップ */
}
</style>
