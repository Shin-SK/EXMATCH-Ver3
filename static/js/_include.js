document.addEventListener("DOMContentLoaded", () => {
    const includes = document.querySelectorAll("[data-include]");

    const loadPart = async (element) => {
        const file = element.getAttribute("data-include");
        const path = `assets/parts/${file}.html`;

        try {
            const response = await fetch(path);
            if (!response.ok) throw new Error(`Failed to load ${path}`);
            const content = await response.text();

            // 動的にHTMLを挿入
            element.innerHTML = content;

            // drawer再初期化
            if (typeof $ !== "undefined" && $.fn.drawer) {
                console.log("Reinitializing drawer...");
                $(".drawer").drawer(); // 再初期化
                console.log("Drawer reinitialized successfully!");
            } else {
                console.error("jQuery or drawer.js not loaded.");
            }
        } catch (error) {
            console.error(`Error loading ${path}:`, error);
        }
    };

    includes.forEach((element) => loadPart(element));
});
