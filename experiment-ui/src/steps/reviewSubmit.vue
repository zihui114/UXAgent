<template>
  <n-card>
    <!-- Persona Summary -->
    <n-card size="small" bordered class="mb-3">
      <template #header>Participant Recruitment</template>

      <n-descriptions :column="1" label-placement="top" bordered>
        <n-descriptions-item label="# of Participants">
          {{ form?.persona?.numSubjects ?? "—" }}
        </n-descriptions-item>
        <n-descriptions-item label="Participant Task">
          {{ form?.persona?.generalIntent || "—" }}
        </n-descriptions-item>
        <n-descriptions-item
          label="Example Persona"
          v-if="form?.persona?.examplePersona"
        >
          {{ form?.persona?.examplePersona }}
        </n-descriptions-item>
      </n-descriptions>

      <n-divider class="my-3">Demographics</n-divider>

      <n-alert v-if="demoTabs.length === 0" type="warning">
        No demographics configured.
      </n-alert>

      <n-tabs v-else type="segment">
        <n-tab-pane
          v-for="(tab, idx) in demoTabs"
          :key="idx"
          :name="tab.name || `field_${idx + 1}`"
          :tab="tab.name || `Field ${idx + 1}`"
        >
          <n-data-table :columns="distColumns" :data="tab.rows" size="small" />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <!-- Experiment Summary -->
    <n-card size="small" bordered class="mb-3">
      <template #header>Experiment</template>
      <n-descriptions :column="1" label-placement="left" bordered>
        <n-descriptions-item label="URL of Website Being Tested">
          {{ form?.experiment?.startUrl || "—" }}
        </n-descriptions-item>
        <n-descriptions-item label="Max Steps">
          {{ form?.experiment?.maxSteps ?? "—" }}
        </n-descriptions-item>
        <n-descriptions-item label="# of Parellel Agents">
          {{ form?.experiment?.concurrency ?? "—" }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- Survey (minimal view) -->
    <n-card size="small" bordered class="mb-3">
      <template #header>Questionnaire</template>

      <!-- Invalid JSON -->
      <n-alert
        v-if="!questionnaireObject"
        type="error"
        title="Invalid Questionnaire JSON"
        class="mb-2"
      >
        Could not parse <code>form.survey.questionnaire</code>. Go back to
        Survey to fix it.
      </n-alert>

      <!-- Empty -->
      <n-alert v-else-if="qCount === 0" type="warning" class="mb-2">
        No questions configured.
      </n-alert>

      <!-- Questions list -->
      <n-list v-if="questionnaireObject && qCount > 0" class="q-list">
        <n-list-item v-for="item in qItems" :key="item.id">
          <div class="q-row">
            <div class="q-num">Q{{ item.idx }}</div>
            <div class="q-main">
              <div class="q-prompt">{{ item.prompt || "(no prompt)" }}</div>
              <div class="q-meta">
                <n-tag size="small" type="info">
                  {{
                    item.type === "multiple_choice"
                      ? "Multiple Choice"
                      : "Short Text"
                  }}
                </n-tag>

                <template
                  v-if="item.type === 'multiple_choice' && item.options.length"
                >
                  <div class="row">
                    <span class="opts-label">Options:</span>
                  </div>
                  <ul>
                    <li v-for="(opt, i) in item.options" :key="i">
                      <n-tag size="small">
                        {{ opt }}
                      </n-tag>
                    </li>
                  </ul>
                </template>
              </div>
            </div>
          </div>
        </n-list-item>
      </n-list>
    </n-card>

    <template #action>
      <div class="card-nav">
        <n-button tertiary @click="nav?.prev?.()" :disabled="submitting">
          <n-icon><MdArrowRoundBack /></n-icon> Back
        </n-button>
        <div class="right-actions">
          <n-button type="success" @click="submit" :loading="submitting">
            Confirm and Run
          </n-button>
        </div>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { inject, computed, ref, h } from "vue";
import { useMessage, NProgress, useDialog } from "naive-ui";
import { FORM_KEY, NAV_KEY, type WizardForm, type WizardNav } from "../types";
import { MdArrowRoundBack } from "@vicons/ionicons4";
import { buildRunPayload } from "../composables/useForm";
import { getPercentsFromWeights } from "../utils/weights.ts";

const form = inject<WizardForm>(FORM_KEY);
const nav = inject<WizardNav>(NAV_KEY);
const message = useMessage();
const dialog = useDialog();

const apiPayload = computed(() => buildRunPayload(form!));

type DistRow = { group: string; weight: number };
/** Turn an array of {name, probability} into rows (probability already 0..1) */
function listToRows(list: { name: string; weight: number }[] = []): DistRow[] {
  const weights = list.map((c) => c.weight);
  const percents = getPercentsFromWeights(weights);

  return list
    .map((c, idx) => ({
      group: c?.name || "(unnamed)",
      weight: percents[idx],
    }))
    .sort((a, b) => b.weight - a.weight);
}

/** Columns with a progress bar cell */
const distColumns = [
  { title: "Group", key: "group" },
  {
    title: "Probability",
    key: "weight",
    width: 240,
    render(row: DistRow) {
      return h(
        "div",
        { style: "display:flex; flex-direction:column; gap:4px;" },
        [
          h("div", `${row.weight.toFixed(1)}%`),
          h(NProgress, {
            percentage: row.weight,
            showIndicator: false,
            height: 10,
            type: "line",
          }),
        ]
      );
    },
  },
];

/** Parse questionnaire once for error surfacing; backend expects an object */
const questionnaireObject = computed(() => {
  try {
    return JSON.parse(form?.survey?.questionnaire ?? "{}");
  } catch {
    return null;
  }
});

const questionnaireParseError = computed(() => {
  const txt = form?.survey?.questionnaire ?? "";
  if (!txt?.trim()) return "Questionnaire is empty";
  try {
    JSON.parse(txt);
    return "";
  } catch (e: any) {
    return String(e?.message ?? e);
  }
});

type QItem = {
  idx: number;
  id: string;
  type: "short_text" | "multiple_choice";
  prompt: string;
  options: string[];
};
const qItems = computed<QItem[]>(() => {
  const q = questionnaireObject.value;
  const list = Array.isArray(q?.questions) ? q!.questions : [];
  return list.map((raw: any, i: number) => ({
    idx: i + 1,
    id: typeof raw?.id === "string" ? raw.id : `q${i + 1}`,
    type: raw?.type === "multiple_choice" ? "multiple_choice" : "short_text",
    prompt: String(raw?.prompt ?? ""),
    options: Array.isArray(raw?.options)
      ? raw.options.map((s: any) => String(s ?? "")).filter(Boolean)
      : [],
  }));
});
const qCount = computed(() => qItems.value.length);

/** Build tabs from unified demographics */
const demoTabs = computed(() => {
  const fields = form?.persona?.demographics || [];
  return fields.map((f) => ({
    name: f?.name || "",
    rows: listToRows(f?.choices || []),
  }));
});

const submitting = ref(false);

async function submit() {
  submitting.value = true;
  try {
    nav?.finish?.();
  } catch (e: any) {
    console.error(e);
    dialog.error(`Submit failed: ${e?.message ?? e}`);
  } finally {
    submitting.value = false;
  }

  dialog.success({
    title: "Study Successfully Created!",
    content:
      "Study is now running in the background.",
  });
}
</script>

<style scoped>
.q-list {
  margin-top: 4px;
}
.q-row {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
  align-items: start;
}
.q-num {
  width: 48px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-weight: 600;
  font-size: 12px;
  background: var(--n-color, rgba(0, 0, 0, 0.04));
}
.q-main {
  display: grid;
  gap: 6px;
}
.q-prompt {
  font-weight: 600;
}
.q-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
}
.dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.4;
}
.opts-label {
  opacity: 0.7;
}

.mb-3 {
  margin-bottom: 12px;
}
.mt-2 {
  margin-top: 8px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.subhead {
  font-weight: 600;
  margin-bottom: 4px;
}
.card-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.right-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
