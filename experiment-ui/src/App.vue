<template>
  <n-config-provider>
    <n-dialog-provider>
      <n-message-provider>
        <TopProgressBar
        :active="progressActive"
        @done="progressActive = false"
        @height="barHeight = $event"
        />
        <n-layout
          class="min-h-screen"
          :style="{ paddingTop: `${barHeight}px` }"
        >
          <n-layout-header bordered>
            <div class="container">
              <n-space vertical>
                <n-steps :current="nav.current.value" :status="currentStatus">
                  <n-step
                    title="Participant Recruitment"
                    description="Configure participant demographics"
                  />
                  <n-step
                    title="Survey"
                    description="Provide a questionnaire"
                  />
                  <n-step title="Review" description="Confirm & Run" />
                </n-steps>
              </n-space>
            </div>
          </n-layout-header>

          <n-layout-content>
            <div class="container content">
              <transition name="fade" mode="out-in">
                <component
                  :is="stepComponents[nav.current.value - 1]"
                  :key="nav.current.value"
                />
              </transition>
            </div>
          </n-layout-content>
        </n-layout>
      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { provide, ref } from "vue";
import type { StepsProps } from "naive-ui";
import { FORM_KEY, NAV_KEY, type WizardNav } from "./types";
import { createWizardForm, submitWizardForm } from "./composables/useForm";
import TopProgressBar from "./components/topProgressBar.vue";
import { useRouteQuery } from "@vueuse/router";

// ---- steps ----
import personas from "./steps/personas.vue";
import survey from "./steps/survey.vue";
import reviewSubmit from "./steps/reviewSubmit.vue";

// ---- shared form ----
const form = createWizardForm();
provide(FORM_KEY, form);

// --- NEW: define barHeight ---
const barHeight = ref(0);

// ---- nav ----
const steps = 3;
// const current = ref<number>(1);
const current = useRouteQuery("step", 1, { transform: Number });
const currentStatus = ref<StepsProps["status"]>("process");

const progressActive = ref(false);

const next = () => {
  if (current.value < steps) current.value++;
};
const prev = () => {
  if (current.value > 1) current.value--;
};
const finish = async () => {
  try {
    console.log("Top bar activated"); // should fire on click
    progressActive.value = true; // show top bar
    await submitWizardForm(form); // triggers POST /run
    // optionally keep the bar up until @done fires (auto-hide on 100%)
  } catch (e: any) {
    progressActive.value = false; // hide if submit failed
    window.alert(e?.message ?? "Submit failed");
  }
};

const nav: WizardNav = { current, steps, next, prev, finish };
provide(NAV_KEY, nav);

const stepComponents = [personas, survey, reviewSubmit];
</script>

<style scoped>
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
}
.content {
  padding: 24px 16px;
  min-height: 52vh;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
