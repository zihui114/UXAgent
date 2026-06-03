#!/bin/bash
uv run -m src.simulated_web_agent.main \
  --persona "$(cat persona_old_latest.txt)" \
  --intent "你最近想找一些低負擔、方便食用的健康食品作為日常補充，因此打開娘家購物網站，希望從中找到一款可以補充蛋白質的點心零食。在搜尋與瀏覽商品的過程中，會點進商品頁面查看商品特色，並確認商品特色中是否有標示具備「豐富蛋白質」，以判斷是否符合需求。若商品提供多種口味，會進一步瀏覽與比較不同口味後再做選擇。另外，希望商品單價在 250 元以內，並選擇同一款商品購買兩包，一包送人、一包自己食用。當確認購物車中商品符合需求後，結束此次操作。" \
  --start-url "file:///Users/linzihui/Desktop/%E5%A4%A7%E5%9B%9B%E4%B8%8B/web_new/UXAgent_testing_web/index.html" \
  --max-steps 20 \
  --headed
