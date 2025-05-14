// 全ての .loop 要素を取得
document.querySelectorAll(".newface .loop").forEach(loop => {
    const boxes = loop.querySelectorAll(".box"); // 現在の box 要素を取得
    const boxCount = boxes.length; // 現在の box 数
    const template = [...boxes]; // 既存の box をテンプレート化

    // box が10個になるまで繰り返し追加
    for (let i = 0; i < 10 - boxCount; i++) {
        const clone = template[i % template.length].cloneNode(true); // テンプレートを複製
        loop.appendChild(clone); // loop コンテナに追加
    }
});

// 全ての .feed .loop 要素を取得
document.querySelectorAll(".feed .loop").forEach(loop => {
    const boxes = loop.querySelectorAll(".box"); // 現在の box 要素を取得
    const boxCount = boxes.length; // 現在の box 数
    const template = [...boxes]; // 既存の box をテンプレート化

    // 最後の数字を取得（例: smp3 → 3）
    let currentImageNumber = Math.max(
        ...Array.from(loop.querySelectorAll(".box img")).map(img => {
            const match = img.src.match(/smp(\d+)/);
            return match ? parseInt(match[1], 10) : 0; // 数字を抽出
        })
    );

    // box が10個になるまで繰り返し追加
    for (let i = 0; i < 10 - boxCount; i++) {
        const clone = template[i % template.length].cloneNode(true); // テンプレートを複製

        // 複製されたbox内の画像パスを変更
        const img = clone.querySelector(".image img");
        if (img) {
            currentImageNumber += 1; // 数字をインクリメント
            img.src = img.src.replace(/smp\d+/, `smp${currentImageNumber}`); // パスを置き換え
        }

        loop.appendChild(clone); // loop コンテナに追加
    }
});
