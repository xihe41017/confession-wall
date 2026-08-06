<script setup>
import { useRoute } from 'vue-router'
import { auth } from '../store/auth'
import { site } from '../store/site'
import { avatarColor } from '../utils'

const route = useRoute()

const links = [
  { to: '/', label: '墙' },
  { to: '/post', label: '发布' },
]
</script>

<template>
  <header class="navbar">
    <router-link to="/" class="brand">🏫 {{ site?.site_name || '校园墙' }}</router-link>
    <nav class="nav-links">
      <router-link
        v-for="l in links"
        :key="l.to"
        :to="l.to"
        class="nav-link"
        :class="{ active: route.path === l.to }"
      >
        {{ l.label }}
      </router-link>
      <router-link
        to="/account"
        class="nav-account"
        :class="{ active: route.path.startsWith('/account') || route.path.startsWith('/admin') }"
      >
        <span v-if="auth.user" class="mini-avatar" :style="{ background: avatarColor(auth.user.nickname) }">
          {{ (auth.user.nickname || auth.user.username)[0] }}
        </span>
        <span v-else class="mini-avatar">👤</span>
      </router-link>
    </nav>
  </header>
</template>
