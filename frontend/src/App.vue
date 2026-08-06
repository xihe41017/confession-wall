<script setup>
import NavBar from './components/NavBar.vue'
import HeartBg from './components/HeartBg.vue'
import ToastHost from './components/ToastHost.vue'
</script>

<template>
  <div class="app-shell">
    <HeartBg />
    <NavBar />
    <main class="page">
      <router-view />
    </main>
    <footer class="site-footer">用一句话，温暖一段青春 💗</footer>
    <ToastHost />
  </div>
</template>
