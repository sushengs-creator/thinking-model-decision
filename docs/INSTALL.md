# 安装、检查与更新

推荐先阅读[仓库首页的一句话安装方式](../README.md)。本项目交付的是完整Skill文件夹，需要由支持Skill的AI助手读取和执行。

## 方法一：让Codex安装

复制到Codex：

```text
请使用 skill-installer 安装：
https://github.com/sushengs-creator/thinking-model-decision/tree/main/skills/thinking-model-decision
安装后检查 thinking-model-decision 的版本。如果已经存在，先核对版本和本地新增内容，不要直接覆盖。
```

工具会按自己的安装流程获取仓库中的技能目录。需要联网或本地目录权限时，按客户端提示处理。安装成功后，下一轮即可尝试：

```text
用 $thinking-model-decision 帮我分析一个问题。请先逐步追问，最终给我决策报告。
```

看到技能名仍不等于模型已正确运作；可以用下面的简单请求试用：

```text
用 $thinking-model-decision 帮我梳理：我学一门技能几个月了，现在不知道该不该继续。
```

正常情况下，它会先承接你的困惑，提出一个影响判断的问题，等待回答；不会一开始给你一整套问卷，或没有背景就劝你坚持、放弃。

## 方法二：下载后手动放入技能目录

1. 在GitHub仓库页面选择 **Code → Download ZIP**，也可以[直接下载main分支ZIP](https://github.com/sushengs-creator/thinking-model-decision/archive/refs/heads/main.zip)。
2. 解压，找到 `skills/thinking-model-decision`。
3. 把**整个 thinking-model-decision 文件夹**放进Codex的技能目录。不要只复制 `SKILL.md`，模型卡、原文、索引和脚本都需要保留。
4. 默认目录是 `~/.codex/skills/`。Windows通常对应 `%USERPROFILE%\.codex\skills\`；如果你设置过 `CODEX_HOME`，则使用该目录下的 `skills`。
5. 最终应能找到 `skills/thinking-model-decision/SKILL.md`，而不是再套一层同名文件夹。
6. 下一轮对话显式调用 `$thinking-model-decision`；若客户端尚未发现新文件，刷新或重开客户端后再检查目录。

这里说明的是Codex的技能目录。其他客户端的安装路径和发现规则以其自身文档为准，本项目没有承诺跨客户端自动兼容。

## 可选：命令行安装

如果你的Codex安装带有系统 `skill-installer`，可以在macOS或Linux终端使用其官方辅助脚本：

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo sushengs-creator/thinking-model-decision \
  --path skills/thinking-model-decision
```

此命令需要Python和网络；辅助脚本不随本仓库重复打包。如果该路径不存在，请改用上面的对话安装或手动复制方式，不必为了安装此Skill另配一套开发环境。

## 检查完整性

让助手读取技能目录中的 `references/library-state.json`，确认当前版本和模型数量。需要进一步检查且有Python 3.9及以上版本时，可运行：

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/thinking-model-decision/scripts/library.py" validate
```

本次公开版的预期是：Skill版本1.2.0、125个用户模型、125张操作卡、100个WW条目，校验无错误。后续版本新增模型后，数量以对应版本为准。

无需额外Python依赖；维护脚本使用标准库。AI助手的对话与推理能力由你使用的平台提供。

## 更新已安装版本

内置安装器遇到同名目录会停止，不会替你安全合并自己的改动。更新时可以让助手执行：

```text
请检查 thinking-model-decision 的本地版本和这个仓库的最新版本：
https://github.com/sushengs-creator/thinking-model-decision
先识别并备份我新增的文稿、卡片及本地修订，再在临时目录下载新版；
比较差异、保留我的有效修改，完成校验后再更新安装目录。
```

如果没有任何本地修改，可先把旧文件夹移到技能目录之外留作备份，再放入完整新版。不要把两个同名技能同时留在发现目录，也不要把新旧文件随意覆盖混合。

更新公开版，不会自动把你自己的新增模型上传给作者；若要贡献，请另行提交Pull Request。

## 常见问题

**为什么只下载文件还不能聊天？**

它是供AI助手调用的技能资料，不含模型服务或独立应用。请在支持Skill的客户端安装后使用。

**为什么提示已经存在？**

这是安装器的覆盖保护。先确认是否有本地改动，再按更新步骤处理，不要直接删除自己的模型库。

**是否要填写API Key？**

本仓库没有自己的API Key设置。你所用AI客户端本身可能需要登录、订阅或其他访问条件。

**为什么未立即出现？**

检查是不是放在正确的技能目录、是否保留完整文件夹，再在下一轮显式调用；仍不可见时刷新客户端并按其自身技能说明排查。

下一步：[详细使用指南](USAGE.md)。
