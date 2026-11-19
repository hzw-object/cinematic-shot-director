# 参考片镜头转译

## 先拿可核实的观察

输入可以是参考视频、连续帧、时间码笔记，或 `rea-video` 的报告。已有报告时先读摘要和所需镜头，必要时回看对应帧核对。只有原片且 `rea-video` 已可用时，按实际任务复用它的抽帧、拆解或故事板能力。工具缺失时用可访问的原片或其他抽帧方式推进。只有单张图片时分析该帧的构图、机位线索和光影。时间变化、切点和声音靠可访问的连续帧、视频、音轨或用户提供的记录来确认，并标明证据来源。

已有 `breakdown.json` 时，可运行 `rea-video summary path/to/breakdown.json`。要核对某段的相机移动，可运行 `rea-video tiles reference.mp4 --start 4 --end 7 --every 0.25 -o frames.jpg`，将路径和时间段替换为实际值。按任务选采样间隔，快速切换或短动作回看原片或加密抽帧。

对有代表性的镜头保留 `参考时间段 | 可见/听到的线索 | 手法及叙事作用 | 推断或待确认`。焦距、光具、设备、后期手法和声音来源仅凭成片经常只能估计。遇到画面放大时，前后景相对位置和视差变化可辅助区分机位移动、变焦和后期裁切。截图、转码色差等限制影响判断时写到对应镜头旁。

## 把手法移到新场景

将每个参考点映射到新的镜头 ID，并解释新场景里的对应节拍。例如参考片用横移露出门后的人，新场景可用演员侧身露出桌上的车票，保留延迟揭示的时机。原动作位置、相机路径或光位不可用时，给一个保留相同信息顺序的拍法。角色、场地、道具、台词和视觉内容随用户的新题材设计。

实拍交接用机位和拍摄顺序。AI 交接用干净关键帧和动态提示词。用户明确要现有工具的自动接力时，核实本地命令和真实输入格式再交接。`rea-video` 与 `capsule-cinema` 已接好时按当前集成文档操作，先检查镜头清单、参考资产和生成路线。纯参考片分析用证据表和结论即可。

## 方法参考

- [Directing Cinematic Storyboards](https://github.com/hosnye/directing-cinematic-storyboards) 的场景地理、连续性和剪辑覆盖组织。
- [Shot Director](https://github.com/AustinZ21/cinematic-skills/tree/main/skills/shot-director) 的运镜起止状态、速度和动机。
- [Storyboard Director](https://github.com/wjq616919/codex-skills/tree/main/storyboard-director) 的戏剧节拍、可读动作和道具状态检查。
- [Storyboard Video Prompts](https://github.com/jianghuancn/codex-video-skills/tree/main/skills/storyboard-video-prompts) 的参考图绑定、分镜画格与动态提示词衔接。
