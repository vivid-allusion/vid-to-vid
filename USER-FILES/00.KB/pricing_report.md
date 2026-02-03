# FAL.ai Video Generation Pricing Leaderboard

## Complete Pricing Leaderboard (Cheapest to Most Expensive)

| Rank | Model                 | Resolution | Duration | Total Price | Price/Second | Price/Frame (30fps) | 10-Min Video Cost |
| ---- | --------------------- | ---------- | -------- | ----------- | ------------ | ------------------- | ----------------- |
| 1    | **WAN-v2.2-Turbo**    | 480p       | 5s       | $0.05       | $0.010*      | $0.00033            | $6.00†            |
| 2    | **WAN-v2.2-Turbo**    | 580p       | 5s       | $0.075      | $0.015*      | $0.00050            | $9.00†            |
| 3    | **WAN-v2.2-Turbo**    | 720p       | 5s       | $0.10       | $0.020*      | $0.00067            | $12.00†           |
| 4    | **Framepack-F1**      | 480p       | 5s       | $0.10       | $0.020*      | $0.00067            | $12.00†           |
| 5    | Seedance-Lite         | 512p       | 5s       | ~$0.10      | $0.020       | $0.00067            | $12.00†           |
| 6    | Hailiuo2-Speed        | 512p       | 6s       | $0.102      | $0.017       | $0.00057            | $10.20            |
| 7    | Hailiuo2-Std          | 512p       | 6s       | $0.102      | $0.017       | $0.00057            | $10.20            |
| 8    | Seedance-Pro          | 512p       | 5s       | ~$0.14      | $0.028       | $0.00093            | $16.80†           |
| 9    | **Framepack**         | 480p       | 5s       | $0.15       | $0.030*      | $0.00100            | $18.00†           |
| 10   | Seedance-Lite         | 720p       | 5s       | $0.18       | $0.036       | $0.00120            | $21.60†           |
| 11   | Hailiuo2-Std          | 768p       | 6s       | $0.27       | $0.045       | $0.00150            | $27.00            |
| 12   | Seedance-Pro          | 720p       | 5s       | ~$0.28      | $0.056       | $0.00187            | $33.60†           |
| 13   | **WAN-v2.2-Standard** | Default    | 5s       | $0.3125     | $0.0625      | $0.00208            | $37.50            |
| 14   | Seedance-Lite         | 1080p      | 5s       | ~$0.45      | $0.090       | $0.00300            | $54.00†           |
| 15   | Hailiuo2-Pro          | Default    | 6s       | $0.48       | $0.080       | $0.00267            | $48.00            |
| 16   | Seedance-Pro          | 1080p      | 5s       | $0.62       | $0.124       | $0.00413            | $74.40†           |
| 17   | **Veo3-Fast-Mute**    | Default    | 5s       | $1.35       | $0.270       | $0.00900            | $162.00           |
| 18   | Kling-Master          | Default    | 5s       | $1.40       | $0.280       | $0.00933            | $168.00‡          |
| 19   | **Veo3-Fast-Sound**   | Default    | 5s       | $2.00       | $0.400       | $0.01333            | $240.00           |
| 20   | **Veo2**              | Default    | 5s       | $2.50       | $0.500       | $0.01667            | $300.00§          |
| 21   | Veo3-Mute             | Default    | 5s       | $2.50       | $0.500       | $0.01667            | $300.00           |
| 22   | Veo3-Sound            | Default    | 5s       | $3.75       | $0.750       | $0.02500            | $450.00           |

†Requires multiple video generations and stitching (models with duration limits)
‡Kling-Master: $1.40 base + $0.28 × 595 additional seconds = $168.00
§Veo2: Limited to 8s max, would require 75 separate videos

**Note:** Bold entries indicate newly added models from the latest update.

## Price Comparison Analysis

### 10-Minute Video Cost Analysis

Creating a 10-minute (600 second) video reveals dramatic price differences:

- **Most Affordable**: WAN-v2.2-Turbo @ 480p costs only **$6.00** (75x cheaper than most expensive)
- **Best Value**: Hailiuo2-Speed/Std @ 512p at **$10.20** for continuous generation
- **Mid-Range Options**: WAN-v2.2-Standard and Hailiuo2-Pro at **$48.00**
- **Premium Territory**: Anything above $100 for 10 minutes (Veo3-Fast-Mute and above)
- **Luxury Tier**: Veo3-Sound at **$450** for 10 minutes of audio-enabled video

**Important Notes on Duration Limits:**

- Some models have maximum duration limits requiring video stitching
- Veo2 is limited to 8 seconds max, requiring 75 separate generations
- Models marked with † require multiple generations and post-processing

### Price Ranges by Tier

| Tier              | Price Range (per frame @ 30fps) | Models                                                         |
| ----------------- | ------------------------------- | -------------------------------------------------------------- |
| **Ultra Budget**  | < $0.0007                       | WAN Turbo variants, Hailiuo2 512p                              |
| **Budget**        | $0.0007 - $0.002                | Seedance-Lite, most Seedance variants                          |
| **Mid-Range**     | $0.002 - $0.01                  | WAN Standard, Hailiuo2-Pro, Seedance-Pro 1080p, Veo3-Fast-Mute |
| **Premium**       | $0.01 - $0.02                   | Kling-Master, Veo3-Fast-Sound, Veo2                            |
| **Ultra Premium** | > $0.02                         | Veo3 with/without sound                                        |

### Key Findings

1. **WAN-v2.2-Turbo @ 480p** is the absolute cheapest at $0.05 per video
2. Price increases **75x** from cheapest (WAN Turbo 480p) to most expensive (Veo3-Sound)
3. Resolution scaling typically doubles the price (480p → 720p, 720p → 1080p)
4. Audio capability adds 40-50% to the cost in Veo3 models
5. The new Veo3-Fast variants are 35-45% cheaper than standard Veo3

### Budget Optimization Guide

| Budget | Best Choice                                 | Videos You Can Generate |
| ------ | ------------------------------------------- | ----------------------- |
| $10    | WAN-v2.2-Turbo @ 480p                       | 200 videos              |
| $25    | WAN-v2.2-Turbo @ 720p or Framepack-F1       | 250 videos              |
| $50    | Framepack-F1 or Seedance-Lite @ 720p        | 277-500 videos          |
| $100   | Mix of Framepack variants and Seedance-Lite | 500-1000 videos         |
| $500   | Seedance-Pro @ 1080p                        | 806 videos              |
| $1000  | Kling-Master or Veo2                        | 400-714 videos          |

### Duration-Based Pricing Models

| Model Type            | Pricing Structure                     | Best For                         |
| --------------------- | ------------------------------------- | -------------------------------- |
| **Fixed Price**       | WAN Turbo, Framepack variants         | Short, standardized content      |
| **Per Second**        | Hailiuo2, WAN Standard, Veo3 variants | Variable length content          |
| **Base + Additional** | Kling-Master, Veo2                    | Known duration requirements      |
| **Token-Based**       | Seedance variants                     | Resolution-specific optimization |

---

*Last updated: Added Framepack and Framepack-F1 models, updated WAN-v2.2-Standard pricing*