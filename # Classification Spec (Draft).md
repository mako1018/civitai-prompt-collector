# Classification Spec (Draft)

Categories: NSFW / style / lighting / composition / mood / technical
Fallback: basic

Keyword seeds（lower-case 部分一致）
NSFW: nsfw, nude, nudity, explicit
style: anime, watercolor, oil painting, sketch, cyberpunk, baroque
lighting: rim light, backlight, volumetric, hdr lighting, ambient light
composition: rule of thirds, close-up, wide shot, portrait, landscape
mood: melancholic, dark, vibrant, dreamy, energetic, tranquil
technical: 8k, hdr, ultra-detailed, depth of field, dof, photorealistic, highres

Precedence:
1. NSFW まず判定
2. 他カテゴリ複数可
3. 該当なし → basic
4. 後で embedding + cluster で補強

Output example:
```
{
  "id": "xxx",
  "prompt": "...",
  "categories": ["style","lighting"],
  "scores": { "style":1.0, "lighting":0.8 },
  "meta": { "source":"civitai","collected_at":"ISO8601" }
}
```