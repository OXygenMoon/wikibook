<script setup>
import DifficultyBadge from '../DifficultyBadge.vue';

const props = defineProps({
  problem: { type: Object, required: true },
});
const emit = defineEmits(['back', 'openCode', 'openSubmit', 'openSubmissions', 'openSubmission']);
</script>

<template>
  <div class="grid grid-cols-1 xl:grid-cols-[1fr,20rem] gap-6 items-start">
    <main class="oj-panel p-6 md:p-8">
      <div class="border-b border-stone-200 dark:border-white/10 pb-6 mb-6">
        <div class="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p class="text-xs font-black tracking-[0.3em] uppercase text-cyan-600 mb-2">Problem {{ problem.code }} · UID {{ problem.uid }}</p>
            <h1 class="text-3xl md:text-4xl font-black text-stone-900 dark:text-stone-100">{{ problem.title }}</h1>
          </div>
          <span v-if="!problem.visible" class="badge badge-ghost">隐藏题</span>
        </div>
        <div class="flex gap-2 flex-wrap mt-5">
          <DifficultyBadge :difficulty="problem.difficulty" />
          <span class="badge badge-outline">{{ problem.timeLimitMs }}ms</span>
          <span class="badge badge-outline">{{ problem.memoryLimitMb }}MB</span>
          <span v-if="problem.source" class="badge badge-outline">{{ problem.source }}</span>
        </div>
      </div>

      <section v-if="problem.hiddenForViewer" class="oj-vue-alert oj-vue-alert--error">
        {{ problem.hiddenMessage }}
      </section>

      <section v-else class="problem-prose" v-html="problem.statementHtml"></section>

      <section v-if="!problem.hiddenForViewer && problem.hasAstGoals" class="mt-8 oj-panel p-5">
        <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100 mb-4">满星语法目标</h2>
        <ol class="list-decimal pl-5 space-y-2 text-stone-700 dark:text-stone-200">
          <li v-for="goal in problem.astGoals" :key="goal.id || goal.description">{{ goal.description }}</li>
        </ol>
      </section>

      <section v-if="!problem.hiddenForViewer && !problem.statementHasSamplePairs" class="mt-8">
        <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100 mb-4">样例</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <template v-for="(sample, index) in problem.sampleCases" :key="index">
            <div class="sample-box oj-panel p-4">
              <div class="flex items-center justify-between mb-3">
                <h3 class="font-black text-stone-900 dark:text-stone-100">输入 {{ index + 1 }}</h3>
                <span class="text-xs text-stone-400">score {{ sample.score }}</span>
              </div>
              <pre>{{ sample.input }}</pre>
            </div>
            <div class="sample-box oj-panel p-4">
              <h3 class="font-black text-stone-900 dark:text-stone-100 mb-3">输出 {{ index + 1 }}</h3>
              <pre>{{ sample.expectedOutput }}</pre>
            </div>
          </template>
          <div v-if="!problem.sampleCases.length" class="oj-panel p-6 text-stone-400 md:col-span-2">这道题暂时没有公开样例。</div>
        </div>
      </section>

      <section v-if="!problem.hiddenForViewer && problem.visibleFiles.length" class="mt-8">
        <h2 class="text-2xl font-black text-stone-900 dark:text-stone-100 mb-4">文件</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <a v-for="file in problem.visibleFiles" :key="file.id" :href="file.filePath" target="_blank" class="oj-panel p-4 hover:border-cyan-400 transition-colors">
            <div class="font-bold text-stone-900 dark:text-stone-100">{{ file.filename }}</div>
            <div class="text-xs text-stone-400 mt-1">{{ file.fileSizeKb }} KB</div>
          </a>
        </div>
      </section>
    </main>

    <aside class="oj-panel p-5 sticky top-24">
      <h2 class="text-xl font-black text-stone-900 dark:text-stone-100 mb-4">题目信息</h2>
      <div class="meta-line"><span class="text-stone-500">UID</span><span class="font-mono font-bold">{{ problem.uid }}</span></div>
      <div class="meta-line"><span class="text-stone-500">编号</span><span class="font-mono font-bold">{{ problem.code }}</span></div>
      <div class="meta-line"><span class="text-stone-500">难度</span><DifficultyBadge :difficulty="problem.difficulty" /></div>
      <div class="meta-line"><span class="text-stone-500">时间限制</span><span class="font-bold">{{ problem.timeLimitMs }} ms</span></div>
      <div class="meta-line"><span class="text-stone-500">内存限制</span><span class="font-bold">{{ problem.memoryLimitMb }} MB</span></div>
      <div class="meta-line"><span class="text-stone-500">语言</span><span class="font-bold text-right">{{ problem.allowedLanguages }}</span></div>
      <div v-if="problem.canManage" class="meta-line"><span class="text-stone-500">隐藏测试点</span><span class="font-bold">{{ problem.hiddenCaseCount }}</span></div>
      <div class="pt-5 flex flex-col gap-3">
        <a v-if="problem.canCode" :href="problem.urls.code" class="btn btn-secondary rounded-lg" @click.prevent="emit('openCode', problem.slug, problem.urls.code)"><i class="fas fa-code" aria-hidden="true"></i> 在线编码</a>
        <a v-if="problem.canSubmit" :href="problem.urls.submit" class="btn btn-primary rounded-lg" @click.prevent="emit('openSubmit', problem.slug, problem.urls.submit)"><i class="fas fa-paper-plane" aria-hidden="true"></i> 提交代码</a>
        <a :href="problem.urls.submissions" class="btn btn-outline rounded-lg" @click.prevent="emit('openSubmissions', problem.urls.submissions.replace('/oj/submissions', '/oj/submissions.json'))">
          <i class="fas fa-list-check" aria-hidden="true"></i> 提交记录
        </a>
        <a v-if="problem.canManage" :href="problem.urls.adminEdit" class="btn btn-ghost rounded-lg"><i class="fas fa-edit" aria-hidden="true"></i> 编辑题目</a>
      </div>
      <div v-if="problem.latestTask" class="mt-5 rounded-lg border border-stone-200 dark:border-white/10 p-4">
        <div class="text-xs text-stone-400 uppercase tracking-widest mb-2">最近提交</div>
        <a :href="problem.latestTask.url" class="font-black text-stone-900 dark:text-stone-100 hover:text-cyan-600" @click.prevent="emit('openSubmission', problem.latestTask.id, problem.latestTask.url)">#{{ problem.latestTask.id }}</a>
        <div class="flex items-center justify-between mt-3">
          <span class="status-chip" :class="`status-chip--${problem.latestTask.statusTone}`">{{ problem.latestTask.statusLabel }}</span>
          <span class="text-sm font-mono">{{ problem.latestTask.passedCount }}/{{ problem.latestTask.totalCount }}</span>
        </div>
      </div>
    </aside>
  </div>
</template>
