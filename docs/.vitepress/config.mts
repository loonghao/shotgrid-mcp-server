import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "ShotGrid MCP Server",
  description: "A Model Context Protocol server for Autodesk ShotGrid",
  base: '/shotgrid-mcp-server/',
  
  head: [
    ['link', { rel: 'icon', href: '/logo.png' }]
  ],

  locales: {
    root: {
      label: 'English',
      lang: 'en',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/' },
          { text: 'Guide', link: '/guide/getting-started' },
          { text: 'API', link: '/api/tools' },
          { text: 'GitHub', link: 'https://github.com/loonghao/shotgrid-mcp-server' }
        ],
        sidebar: {
          '/guide/': [
            {
              text: 'Introduction',
              items: [
                { text: 'Getting Started', link: '/guide/getting-started' },
                { text: 'Installation', link: '/guide/installation' },
                { text: 'Configuration', link: '/guide/configuration' },
              ]
            },
            {
              text: 'Demos',
              items: [
                { text: 'Editor Setup', link: '/guide/demos/editor-setup' },
                { text: 'Query & Visualize', link: '/guide/demos/query-visualize' },
                { text: 'Batch Operations', link: '/guide/demos/batch-operations' },
                { text: 'TimeLog Statistics', link: '/guide/demos/timelog-statistics' },
                { text: 'WeCom Integration', link: '/guide/demos/wecom-integration' },
              ]
            }
          ],
          '/api/': [
            {
              text: 'API Reference',
              items: [
                { text: 'Tools Overview', link: '/api/tools' },
                { text: 'CRUD Operations', link: '/api/crud' },
                { text: 'Batch Operations', link: '/api/batch' },
                { text: 'Notes & Playlists', link: '/api/notes-playlists' },
              ]
            }
          ]
        }
      }
    },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      themeConfig: {
        nav: [
          { text: '首页', link: '/zh/' },
          { text: '指南', link: '/zh/guide/getting-started' },
          { text: 'API', link: '/zh/api/tools' },
          { text: 'GitHub', link: 'https://github.com/loonghao/shotgrid-mcp-server' }
        ],
        sidebar: {
          '/zh/guide/': [
            {
              text: '介绍',
              items: [
                { text: '快速开始', link: '/zh/guide/getting-started' },
                { text: '安装', link: '/zh/guide/installation' },
                { text: '配置', link: '/zh/guide/configuration' },
              ]
            },
            {
              text: '演示',
              items: [
                { text: '编辑器配置', link: '/zh/guide/demos/editor-setup' },
                { text: '查询与可视化', link: '/zh/guide/demos/query-visualize' },
                { text: '批量操作', link: '/zh/guide/demos/batch-operations' },
                { text: 'TimeLog 统计', link: '/zh/guide/demos/timelog-statistics' },
                { text: '企业微信集成', link: '/zh/guide/demos/wecom-integration' },
              ]
            }
          ],
          '/zh/api/': [
            {
              text: 'API 参考',
              items: [
                { text: '工具概览', link: '/zh/api/tools' },
                { text: 'CRUD 操作', link: '/zh/api/crud' },
                { text: '批量操作', link: '/zh/api/batch' },
                { text: '笔记与播放列表', link: '/zh/api/notes-playlists' },
              ]
            }
          ]
        }
      }
    }
  },

  themeConfig: {
    logo: '/logo.png',

    socialLinks: [
      { icon: 'github', link: 'https://github.com/loonghao/shotgrid-mcp-server' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-present'
    },

    search: {
      provider: 'local'
    }
  }
})
