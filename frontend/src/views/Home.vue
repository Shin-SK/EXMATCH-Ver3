<!-- src/views/Home.vue -->
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Splide, SplideSlide } from '@splidejs/vue-splide'
import { AutoScroll } from '@splidejs/splide-extension-auto-scroll'
import '@splidejs/splide/css'

const router = useRouter()
const route  = useRoute()

const loginHref = computed(() => {
  const n = route.query.next
  const next = Array.isArray(n) ? n[0] : (n || '')
  return next ? `/login?next=${encodeURIComponent(next)}` : '/login'
})

// 切替
const currentLoop = ref('female')
const setLoop = g => { currentLoop.value = g }

// サンプル画像を生成（/public/img/smp1.webp, smp2.webp… / smp1-m.webp…）
function buildSamples(count, gender='female'){
  const suffix = gender === 'male' ? '-m' : ''
  return Array.from({length: count}, (_,i) => {
    const n = i+1
    return {
      id: `${gender}-${n}`,
      name: 'サンプル',
      age: '--',
      lciq: '--',
      img: `/img/smp${n}${suffix}.webp`,
    }
  })
}

// ここだけで完結：LP用のダミー（見た目サンプル）
const femaleProfiles = ref(buildSamples(10, 'female'))
const maleProfiles   = ref(buildSamples(10, 'male'))

const visibleProfiles = computed(() =>
  currentLoop.value === 'female' ? femaleProfiles.value : maleProfiles.value
)

// 無限流し用に増量（切れ目防止）
const visibleMarqueeProfiles = computed(() => {
  const base = visibleProfiles.value
  const targetLen = Math.max(12, base.length * 2)
  const repeat = Math.ceil(targetLen / base.length)
  const out = Array.from({ length: repeat }, () => base).flat()
  return out.slice(0, targetLen)
})

// スライダー設定（線形オートスクロール）
const carouselOpts = {
  type: 'loop',
  drag: 'free',
  focus: 0,
  arrows: false,
  pagination: false,
  fixedWidth: 200,
  fixedHeight: 200,
  gap: '16px',
  easing: 'linear',
  autoScroll: { speed: 0.7, pauseOnHover: true, pauseOnFocus: true },
  breakpoints: {
    768: { fixedWidth: 160, fixedHeight: 160, gap: '12px' },
    576: { fixedWidth: 140, fixedHeight: 140, gap: '10px' },
  },
}

// LPスクロール解放
onMounted(() => document.body.classList.add('lp-scroll'))
onUnmounted(() => document.body.classList.remove('lp-scroll'))
</script>


<template>
  <section class="home" id="home">
    <!-- header -->
    <div class="header">
      <div class="header__wrap">
        <nav
          class="navbar navbar-expand-md navbar-light border-bottom position-absolute top-0 end-0 start-0"
          style="
            z-index:1000;
            background:rgba(255,255,255,.9);
          ">
          <div class="container-fluid px-3">
            <a class="navbar-brand d-flex align-items-center" href="/">
              <img src="/img/logo.svg" alt="EXMATCH" style="height:40px;" />
            </a>

            <button class="navbar-toggler" type="button"
                    data-bs-toggle="collapse" data-bs-target="#homeNav"
                    aria-controls="homeNav" aria-expanded="false" aria-label="Toggle navigation">
              <IconMenu2 />
            </button>

            <div class="collapse navbar-collapse" id="homeNav">
              <ul class="navbar-nav ms-auto align-items-md-center gap-md-3">
                <li class="nav-item"><a class="nav-link" href="#midashi">特徴</a></li>
                <li class="nav-item"><a class="nav-link" href="#koe">お客様の声</a></li>
                <li class="nav-item"><a class="nav-link" href="#search">お相手検索</a></li>
                <li class="nav-item"><a class="nav-link" href="#price">料金</a></li>
                <li class="nav-item">
                  <a class="btn btn-pink text-white ms-md-2" :href="loginHref">ログイン</a>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </div>
    </div>

    <!-- KV -->
    <section class="kv">
      <div class="kv__wrap">
        <div class="area">
          <div class="box">
            <h2>本気で出会う</h2>
            <h3>
              ちゃんとした人と出会う。<br>
              そのためにちゃんと成長する。<br>
              そんな当たり前ができること。<br>
              ここには、<br>
              適当な出会いはありません。
            </h3>
            <div class="wrap">
              <a class="button" href="/signup">さっそくはじめる</a>
              <a class="login"  :href="loginHref">ログイン</a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CV -->
    <section class="cv" id="cv">
      <div class="cv__wrap">
        <a class="button" href="/signup">さあはじめよう</a>
      </div>
    </section>

    <!-- 見出し -->
    <section class="midashi container" id="midashi">
      <div class="h1">
        本気だけど、手軽に出会いたい。<br>
        そんな願いをかなえました。
      </div>

      <p>
        総合婚活サービスEXMarry®が運営する<br class="d-md-none">マッチングサービスです。<br>
        恋愛偏差値®を使うことで<br class="d-md-none">相手との相性がすぐにわかります。<br>
        本気で、手軽に。<br>
        相性のいい相手としか<br class="d-md-none">出会うことができないサービスです。
      </p>
    </section>

    <!-- Feature -->
    <section class="feature container" id="feature">
      <div class="feature__wrap">
        <div class="area">
          <div class="title">
            <div class="honki">EXMATCHが本気な理由<span>1</span></div>
            <div class="subtitle">恋愛偏差値®で自分の恋愛力を数値化</div>
          </div>

          <div class="outer">
            <div class="box">
              <div class="img"><img src="/img/honki-1.webp" alt=""></div>
              <div class="text">
                <div class="head">漠然とした恋愛はもうおしまい</div>
                <p>
                  LCIQ®による恋愛偏差値®を掲載。数値化された恋愛力をもとに、相性の良い相手からの「いいね」があるはず。自分の恋愛傾向がわかるので、これからの人生に必ず役立ちます。
                </p>
              </div>
            </div>

            <div class="box">
              <div class="img"><img src="/img/honki-2.webp" alt=""></div>
              <div class="text">
                <div class="head">トライサポートで恋愛力を高める</div>
                <p>
                  点数が低くても大丈夫。EXMarryが運営する恋愛力向上プラットフォーム「トライサポート」で自分の恋愛力を高めましょう。
                  恋愛偏差値は何度でも検査可能です。その努力は、必ず実ります。
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="area">
          <div class="title">
            <div class="honki">EXMATCHが本気な理由<span>2</span></div>
            <div class="subtitle">プラスプロフィールで<br class="d-md-none">相手の深い部分を知る</div>
          </div>

          <div class="outer">
            <div class="box">
              <div class="img"><img src="/img/honki-3.webp" alt=""></div>
              <div class="text">
                <div class="head">夜の相性と離婚率は関係している</div>
                <p>性生活の相性はカップルにとってとても重要です。最初から相手の好みを知ることで、すれ違いを防ぎます。</p>
              </div>
            </div>

            <div class="box">
              <div class="img"><img src="/img/honki-4.webp" alt=""></div>
              <div class="text">
                <div class="head">本当の自分で最高の相手と出会える</div>
                <p>実は隠してきたことはもうないはず。恋愛力を高め自分をさらけ出すことで、一生のパートナーと出会えるはずです。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- お客様の声 -->
    <section class="koe container" id="koe">
      <div class="mainTitle">お客様の声</div>
      <div class="area">
        <div class="box">
          <div class="img"><img src="/img/koe-1.webp" alt=""></div>
          <div class="text">
            <div class="head">頑張ったから出会いがあった</div>
            <p>最初は「めんどくさい」と思うこともありましたが、がんばった分だけいい人と出会えると信じてがんばりました。今では頑張ってよかったと思っています</p>
          </div>
        </div>
        <div class="box">
          <div class="img"><img src="/img/koe-2.webp" alt=""></div>
          <div class="text">
            <div class="head">本気で出会いたい</div>
            <p>本気で出会いたかった私にはピッタリのサービスでした。最初は恋愛偏差値が低かったですが、トライサポートのおかげで偏差値もあがり、いい出会いがありました。</p>
          </div>
        </div>
        <div class="box">
          <div class="img"><img src="/img/koe-3.webp" alt=""></div>
          <div class="text">
            <div class="head">適当な人がいないのはいいこと</div>
            <p>本気で出会いたかった私にとっては、ただその時楽しければいい「友達探し」の感じは不要でした。エクスマッチは相手も数値で出ますし、結婚した後も充実した時間を過ごしています。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- お相手検索 -->
    <section class="oaite" id="search">
      <div class="container">
        <div class="mainTitle"><IconHeart />お相手検索</div>
        <div class="row gx-3 gy-0">
          <div class="col-6">
            <button
              class="female btn btn-pink text-white w-100"
              :class="{ active: currentLoop==='female' }"
              @click="setLoop('female')"
            >女性</button>
          </div>
          <div class="col-6">
            <button
              class="male btn btn-primary w-100"
              :class="{ active: currentLoop==='male' }"
              @click="setLoop('male')"
            >男性</button>
          </div>
        </div>

        <div class="oaite__loop mt-3 overflow-hidden">
          <div v-if="loadingPairs" class="loading">読み込み中…</div>
          <div v-else-if="errPairs" class="error">{{ errPairs }}</div>
          <Splide :options="carouselOpts" :extensions="{ AutoScroll }" :key="currentLoop" class="oaite__splide">
            <SplideSlide v-for="u in visibleMarqueeProfiles" :key="`${u.id}-${Math.random()}`">
              <div class="box">
                <a href="/signup"> <!-- 実ユーザーではないのでサインアップへ誘導 -->
                  <div class="image">
                    <img class="blurred" :src="u.img" alt="" />
                    <!-- <div class="info">
                      <div class="name">{{ u.name }}</div>
                      <div class="age">{{ u.age }}</div>
                      <div class="lciq">{{ u.lciq }}</div>
                    </div> -->
                  </div>
                </a>
              </div>
            </SplideSlide>
          </Splide>
        </div>
        
      </div>
    </section>

    <!-- 料金 -->
    <section class="price-home container" id="price">
      <div class="mainTitle">ご利用料金</div>
      <div class="subtitle">
        一般的な結婚相談所での料金は、成婚まで平均して約30万円前後*。<br>
        エクスマッチのスタンダードプランが高いと思うか、安いと感じるか。<br>
        それはあなた次第です。
        <span>*当社調べの中央値。初期費用(約104,500円)、月会費(約21,450円)、成婚料(約220,000円)で計算。</span>
      </div>

      <div class="price-home__wrap">
        <div class="free-area frame-area">
          <div class="box">
            <div class="head">フリー<span>FREE</span></div>
            <div class="wrap">
              <div class="outer">
                <div class="left">
                  <div class="numb-month">0</div>
                  <p>初めて婚活マッチングを利用する方に<br>ピッタリのお試しプラン</p>
                </div>
                <div class="right">
                  <ul class="check">
                    <li>価値観診断</li>
                    <li>価値観マッチ ( 価値観による紹介 )</li>
                    <li>お相手のプロフィールを見る</li>
                    <li>お相手に「いいね！」をする</li>
                    <li>「いいね！」をくれた方とマッチングする ( 無制限 )</li>
                    <li>非表示機能</li>
                    <li>初回メッセージ１通のみ</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="standard-area">
          <div class="catch">
            わずらわしいポイントはありません。<br>
            有料プランは<br class="d-md-none">すべての機能がご利用いただけます。
          </div>

          <div class="plan">
            <div class="inner">1ヶ月プラン</div>
            <div class="numb-month">4,500</div>
          </div>
        </div>

        <div class="pack-area">
          <div class="box">
            <div class="head">3ヶ月パック</div>
            <div class="inner"><div class="getugaku numb-month">3,850</div></div>
            <div class="amount">11,550<span>円</span></div>
            <div class="special agel">
              <div class="wrap">
                <div class="numb">4,620<span>円分</span></div>
                <div class="inner">A-GELポイント<br>プレゼント</div>
              </div>
            </div>
            <div class="special opening">
              <div class="wrap">
                <div class="head">オープニングキャンペーン</div>
                <div class="span">+1ヶ月無料</div>
              </div>
            </div>
          </div>

          <div class="box">
            <div class="head">6ヶ月パック</div>
            <div class="inner"><div class="getugaku numb-month">3,150</div></div>
            <div class="amount">18,900<span>円</span></div>
            <div class="special agel">
              <div class="wrap">
                <div class="numb">7,560<span>円分</span></div>
                <div class="inner">A-GELポイント<br>プレゼント</div>
              </div>
            </div>
            <div class="special opening">
              <div class="wrap">
                <div class="head">オープニングキャンペーン</div>
                <div class="span">+2ヶ月無料</div>
              </div>
            </div>
          </div>

          <div class="box">
            <div class="head">12ヶ月パック</div>
            <div class="inner"><div class="getugaku numb-month">2,450</div></div>
            <div class="amount">29,400<span>円</span></div>
            <div class="special agel">
              <div class="wrap">
                <div class="numb">11,760<span>円分</span></div>
                <div class="inner">A-GELポイント<br>プレゼント</div>
              </div>
            </div>
            <div class="special opening">
              <div class="wrap">
                <div class="head">オープニングキャンペーン</div>
                <div class="span">+3ヶ月無料</div>
              </div>
            </div>
          </div>
        </div>

        <div class="option-area">
          <div class="catch">
            オプションも明朗会計。<br>
            こちらもポイント制ではなく、<br class="d-md-none">お申し込みいただければ<br>
            すぐにご利用いただけます。
          </div>
          <div class="frame-area">
            <div class="box">
              <div class="head">プラスプロフィール</div>
              <div class="wrap">
                <div class="outer">
                  <div class="special left">
                    <div class="normal">
                      <div class="off">50%<br>OFF</div>
                      <div class="numb-month">1,500</div>
                    </div>
                    <div class="sp">
                      <div class="triangle"><span class="material-symbols-outlined">stat_minus_3</span></div>
                      <div class="numb-month">750</div>
                    </div>
                  </div>
                  <div class="right">
                    <ul class="check">
                      <li>性指向などのプラスプロフィールが見れる</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>          
        </div>
      </div>
    </section>

    <!-- セキュリティ -->
    <section class="security container" id="security">
      <div class="container">
        <div class="mainTitle">セキュリティ</div>
        <div class="subtitle">GPSを使っているからこそ、セキュリティは万全。<br>安心してご利用ください。</div>
        <div class="security__wrap">
          <div class="box"><img src="/img/sc1.webp" alt=""><span>プライバシー<br>守ります</span></div>
          <div class="box"><img src="/img/sc2.webp" alt=""><span>悪質ユーザー<br>取り締まり</span></div>
          <div class="box"><img src="/img/sc3.webp" alt=""><span>万全の<br>サポート体制</span></div>
          <div class="box"><img src="/img/sc4.webp" alt=""><span>高額請求<br>なし</span></div>
        </div>
      </div>
    </section>

    
<section class="faq container" id="faq">
  <div class="container">
    <div class="mainTitle">FAQ</div>
    <div class="subtitle">よくある質問をまとめました。<br>ぜひ参照してください。</div>

    <div class="faq__wrap">
      <!-- 1 -->
      <div class="box">
        <div class="q"><div class="title">初期登録にはどのくらいの情報を記入しますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq1"
            aria-expanded="false"
            aria-controls="faq1"
          >
            <span>登録情報と安心バッジ<IconChevronRight /></span>
          </button>
          <div id="faq1" class="collapse mt-2">
            <p>
              EXMATCHは婚活専用マッチングサイトなので、安心感を重視し男女ともに一定の情報の開示が必要になります。<br>
              無料プランや初期登録は6項目で登録できますが、有料プランにお申込みの際はより細かな項目にご記入いただきます。<br>
              証明書類など開示レベルに応じてランクバッチも表記され、安心度が一目で分かる配慮もしています。
            </p>
          </div>
        </div>
      </div>

      <!-- 2 -->
      <div class="box">
        <div class="q"><div class="title">婚活専用とのことですが、相談所のようなアドバイザーがついたりしますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq2"
            aria-expanded="false"
            aria-controls="faq2"
          >
            <span>アドバイザーの有無<IconChevronRight /></span>
          </button>
          <div id="faq2" class="collapse mt-2">
            <p>
              サイト内で個々の活動が完結します。急ぎのサポートはメッセージ機能で対応しますが、<br>
              本格的な伴走を希望される場合は結婚相談所EXMarry®の「12ヶ月成婚パック」をご検討ください。
            </p>
          </div>
        </div>
      </div>

      <!-- 3 -->
      <div class="box">
        <div class="q"><div class="title">証明書類はどのようなものが必要ですか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq3"
            aria-expanded="false"
            aria-controls="faq3"
          >
            <span>必要な提出証明書類<IconChevronRight /></span>
          </button>
          <div id="faq3" class="collapse mt-2">
            <p>
              運転免許証・マイナンバーカード・年収証明（男性）・資格証明書（職業により）・独身証明書などの写真データをご提出ください。
            </p>
          </div>
        </div>
      </div>

      <!-- 4 -->
      <div class="box">
        <div class="q"><div class="title">恋愛偏差値®診断はしないといけませんか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq4"
            aria-expanded="false"
            aria-controls="faq4"
          >
            <span>診断はぜひ受験<IconChevronRight /></span>
          </button>
          <div id="faq4" class="collapse mt-2">
            <p>
              ぜひトライしてください！ 単純なマッチングではなく、同一基準の診断結果を表示することで<br>
              お互いの良い面や不足傾向を把握し、ゆとりあるコミュニケーションが可能になります。
            </p>
          </div>
        </div>
      </div>

      <!-- 5 -->
      <div class="box">
        <div class="q"><div class="title">恋愛偏差値®を向上させるためのアドバイスなどはありますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq5"
            aria-expanded="false"
            aria-controls="faq5"
          >
            <span>偏差値向上サポート<IconChevronRight /></span>
          </button>
          <div id="faq5" class="collapse mt-2">
            <p>
              診断結果をもとに考え方や行動基準をサポートします。無料の記事から有料講座まで幅広くご用意しています。
            </p>
          </div>
        </div>
      </div>

      <!-- 6 -->
      <div class="box">
        <div class="q"><div class="title">プロフィール写真は何枚まで掲載できますか？　また、プランによってボカシはありますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq6"
            aria-expanded="false"
            aria-controls="faq6"
          >
            <span>写真枚数とボカシ<IconChevronRight /></span>
          </button>
          <div id="faq6" class="collapse mt-2">
            <p>
              １枚まで掲載できます（カメラマン撮影が理想）。現在、複数枚写真をアップできるようアップデート中です。バストショットや全身などバリエーションを付けると印象が上がります。<br>
              LCIQのポイント、スクリーンショットを設定していない方は、写真にボカシが入ります。
            </p>
          </div>
        </div>
      </div>

      <!-- 7 -->
      <div class="box">
        <div class="q"><div class="title">しつこい人や横暴な人、目的と違う話をしてくる相手の場合、通報はできますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq7"
            aria-expanded="false"
            aria-controls="faq7"
          >
            <span>通報制度と対応<IconChevronRight /></span>
          </button>
          <div id="faq7" class="collapse mt-2">
            <p>
              通報制度があります。内容・頻度によっては強制退会となる場合もありますので、時間をムダにしないためにもご活用ください。
            </p>
          </div>
        </div>
      </div>

      <!-- 8 -->
      <div class="box">
        <div class="q"><div class="title">友人・知人がいたので見られないよう対策できますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq8"
            aria-expanded="false"
            aria-controls="faq8"
          >
            <span>ブロックで非表示<IconChevronRight /></span>
          </button>
          <div id="faq8" class="collapse mt-2">
            <p>
              ブロック機能を使えば双方で非表示になりますので、相手から見られることはありません。
            </p>
          </div>
        </div>
      </div>

      <!-- 9 -->
      <div class="box">
        <div class="q"><div class="title">なかなかマッチングしませんが対策はありますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq9"
            aria-expanded="false"
            aria-controls="faq9"
          >
            <span>マッチ率アップ術<IconChevronRight /></span>
          </button>
          <div id="faq9" class="collapse mt-2">
            <p>
              まずはプロフィールや写真を見直しましょう。飾らず素直な文面や明るい服装の写真に変更するだけでも変化が見込めます。<br>
              結婚相手探しとして自分の魅せ方を工夫してください。
            </p>
          </div>
        </div>
      </div>

      <!-- 10 -->
      <div class="box">
        <div class="q"><div class="title">婚活する中でもっと自分磨きをしたいと思うことが多いのですが、その辺のサポートはありますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq10"
            aria-expanded="false"
            aria-controls="faq10"
          >
            <span>自分磨き支援有<IconChevronRight /></span>
          </button>
          <div id="faq10" class="collapse mt-2">
            <p>
              グループの「TRY SUPPORT」ポータルサイトで内面・外見を磨く多彩なサービスをご提供しています。<br>
              登録無料でお得に利用できます（東京版／今秋オープン予定）。
            </p>
          </div>
        </div>
      </div>

      <!-- 11 -->
      <div class="box">
        <div class="q"><div class="title">サイト内で結婚相手が見つかった場合に別に費用がかかりますか？</div></div>
        <div class="a">
          <button
            type="button"
            class="title collapsed"
            data-bs-toggle="collapse"
            data-bs-target="#faq11"
            aria-expanded="false"
            aria-controls="faq11"
          >
            成婚時の費用なし<IconChevronRight />
          </button>
          <div id="faq11" class="collapse mt-2">
            <p>
              月会費以外は一切かかりません。安心してステキな出会いを楽しんでください。
            </p>
          </div>
        </div>
      </div>

    </div>
  </div>
</section>



    <!-- バナー -->
    <section class="exm-banner">
      <h2 class="br">
        EXMarryが運営する結婚相談所のご案内です。<br>
        EXMATCHよりも手厚くしっかりサポートを受けながら結婚を考えたい方は<br>
        ぜひご検討ください。
      </h2>
      <a href="#"><img src="/img/banner1.webp" alt=""></a>
    </section>

    <!-- footer -->
    <footer class="footer-home">
      <div class="container">
        <div class="sns">
          <a class="youtube" href="#" target="_blank"><img src="/img/sns-youtube.webp" alt=""></a>
          <a class="tiktok"  href="#" target="_blank"><img src="/img/sns-tiktok.webp"  alt=""></a>
        </div>
        <div class="footer-home__wrap">
          <ul>
            <li><a href="/">会社概要</a></li>
            <li><a href="/">利用規約</a></li>
            <li><a href="/">安心・安全の取り組みとガイド</a></li>
            <li><a href="/">コミュニティガイドライン</a></li>
            <li><a href="/">プライバシーポリシー</a></li>
            <li><a href="/">クッキーポリシー</a></li>
            <li><a href="/">クッキー設定</a></li>
            <li><a href="/">特定商取引法に基づく表示</a></li>
            <li><a href="/">ヘルプ</a></li>
            <li><a href="/">法人･自治体向けサービス</a></li>
            <li><a href="/">採用サイト</a></li>
            <li><a href="/">記事提供元一覧</a></li>
          </ul>
        </div>
        <div class="logo"><a href="/"><img src="/img/logo.svg" alt="Logo"></a></div>
        <div class="cr"><a href="/">&copy; 2024 EXMATCH</a></div>
      </div>
    </footer>
  </section>
</template>

<style scoped>
/* ここでは最低限のみ。レイアウト/色は既存SCSSを適用してください */
.nav-button{ background:transparent; border:0; }
.navbar-toggler{
  border: none;
}
#menu{ display:none; }
#menu.open{ display:block; }
.nav-backdrop{ position:fixed; inset:0; background:rgba(0,0,0,.35); }

/* 横スクロール */
.hscroll{ overflow-x:auto; -webkit-overflow-scrolling:touch; }
.hscroll .box{ flex:0 0 auto; }
.oaite__wrap{ display:flex; gap:12px; padding:8px 0; }

/* PC/SPテキスト切替は既存SCSSに合わせて */
.lead-pc{ display:block; }
.lead-sp{ display:none; }

.oaite__splide :deep(.splide__track){ overflow: visible; }

/* 無限流しを滑らかに */
.oaite__splide :deep(.splide__list){ transition-timing-function: linear; }
/* サンプルは薄いブラー */
.image .blurred{
  filter: blur(4px) saturate(.9);
  transform: scale(1.01);
}
</style>
