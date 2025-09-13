// src/utils/viewport.js
export function mountViewportFix(){
	const set = () => {
		const vh = (window.visualViewport?.height || window.innerHeight);
		document.documentElement.style.setProperty('--app-h', `${vh}px`);
	};
	// 初回＋少し遅延して2回叩くと安定
	set();
	setTimeout(set, 50);
	setTimeout(set, 350);

	// 変化しうるイベントで追従
	window.visualViewport?.addEventListener('resize', set);
	window.visualViewport?.addEventListener('scroll', set); // iOSで高さが変わることがある
	window.addEventListener('orientationchange', set);
	window.addEventListener('resize', set);
}
