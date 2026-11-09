# Stash 去广告覆写（秋风＋墨鱼去开屏＋B站）

给 iOS 版 [Stash](https://stash.wiki/) 用的去广告覆写（.stoverride），由公开的去广告规则合并而成，每天自动从上游重新生成一次。

## 安装

在 iPhone 上点下面的链接，Stash 会打开安装页：

https://link.stash.ws/install-override/raw.githubusercontent.com/CapRnl/stash-adblock/main/adblock.stoverride

也可以在 Stash「覆写 → ＋ → 从 URL 安装」里粘贴：

```
https://raw.githubusercontent.com/CapRnl/stash-adblock/main/adblock.stoverride
```

要去掉开屏广告，Stash 须开启 MitM，并在 iOS「设置」里安装、完全信任 Stash 生成的证书；不开 MitM 时只有秋风规则（按域名拦截）生效。

## 内容

1. [秋风广告规则](https://github.com/TG-Twilight/AWAvenue-Ads-Rule)（Clash 完整版）：覆写里只写引用地址，Stash 每 24 小时自己更新，命中的广告、统计域名直接拒绝。
2. 墨鱼「APP 启动页去广告」与「哔哩哔哩去广告」的 Stash 版（[deezertidal/stash-override](https://github.com/deezertidal/stash-override) 转制，发布在 yfamilys.com）：解密主机、URL 改写、响应体改写、脚本合并去重。

## 生成规则

- 脚本只保留来源可核实的：GitHub 仓库里的原文件，以及 blackmatrix7、ddgksf2013 两位作者的 gist；其他来源（如匿名的 Cloudflare Worker）的脚本连同引用一并去掉。
- 上游的 `rewrite` 键按 Stash 文档改为 `url-rewrite`。
- 生成后自检：格式回读、脚本都有来源、数量没有异常减少；自检不通过时当天不更新，保留上一版。
- 更新由 [.github/workflows/build.yml](.github/workflows/build.yml) 每天运行一次 `build_override.py`，内容有变化才提交。

## 说明

- 规则内容的权利归各原作者所有，这里只做合并和筛选；生成器代码按 MIT 许可发布。
- MitM 会在本机解密所列主机的 HTTPS 流量，覆写里的脚本可以读写这些主机的请求和响应。安装前可先看一遍 `adblock.stoverride` 里的 `mitm` 和 `script-providers`。
