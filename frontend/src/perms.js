// 权限键定义（与后端 app/permissions.py 一致）
export const PERMS = [
  { key: 'content.manage', group: '内容管理', label: '内容审核 / 删除' },
  { key: 'content.pin', group: '内容管理', label: '置顶 / 取消置顶' },
  { key: 'content.edit', group: '内容管理', label: '编辑内容（赞数/对象/昵称）' },
  { key: 'content.ban_ip', group: '内容管理', label: '对内容拉黑 IP' },
  { key: 'comment.edit', group: '评论管理', label: '编辑评论点赞数' },
  { key: 'ban.manage', group: 'IP 黑名单', label: '查看 / 解除 IP 黑名单' },
  { key: 'settings.view', group: '服务器设置', label: '查看服务器设置' },
  { key: 'settings.site_announcement', group: '服务器设置', label: '修改：站点公告' },
  { key: 'settings.moderation_mode', group: '服务器设置', label: '修改：发布需审核开关' },
  { key: 'settings.allow_register', group: '服务器设置', label: '修改：开放注册开关' },
  { key: 'settings.register_approval', group: '服务器设置', label: '修改：注册需激活开关' },
  { key: 'settings.anonymous_post_limit', group: '服务器设置', label: '修改：匿名限发条数' },
]

export const PERM_GROUPS = [...new Set(PERMS.map((p) => p.group))]
