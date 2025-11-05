<template>
  <n-card title="Post Study Survey" size="large">
    <p class="mb-2">
      Design the questionnaire that every LLM Agent participant need to complete
      after interacting with the system.
    </p>

    <n-divider>Questions</n-divider>

    <!-- Empty state -->
    <n-alert
      v-if="questionsForm.questions.length === 0"
      type="info"
      class="mb-2"
    >
      No questions yet.
    </n-alert>

    <n-form ref="formRef" :model="questionsForm">
      <!-- Questions list -->
      <div class="q-list">
        <n-card
          v-for="(q, i) in questionsForm.questions"
          :key="q.uid"
          size="small"
          :title="`Q${i + 1} — ${
            q.type === 'short_text' ? 'Open Ended' : 'Multiple Choice'
          }`"
          class="q-card"
        >
          <div class="field">
            <n-form-item
              label="Type"
              :path="`questions[${i}].type`"
              :rule="{
                required: true,
                message: 'Please select the type',
              }"
              :show-feedback="false"
            >
              <n-radio-group v-model:value="q.type" size="small">
                <n-radio value="short_text">Open Ended</n-radio>
                <n-radio value="multiple_choice">Multiple Choice</n-radio>
              </n-radio-group>
            </n-form-item>
          </div>

          <div class="field">
            <n-form-item
              label="Question"
              :path="`questions[${i}].prompt`"
              :rule="{
                required: true,
                message: 'Please input the question',
                trigger: ['input', 'blur'],
              }"
            >
              <n-input
                v-model:value="questionsForm.questions[i].prompt"
                placeholder="Enter the question…"
                clearable
              />
            </n-form-item>
          </div>

          <div class="field" v-if="q.type === 'multiple_choice'">
            <label class="n-form-item-label n-form-item-label--right-mark"
              ><span class="n-form-item-label__text">Options</span
              ><span style="color: rgb(208, 48, 80)">&nbsp;*</span></label
            >
            <n-form-item
              v-for="(opt, option_index) in q.options"
              :key="option_index"
              :path="`questions[${i}].options[${option_index}]`"
              :rule="{
                required: true,
                message: 'Please input the option',
                trigger: ['input', 'blur'],
              }"
              :show-label="false"
              :show-feedback="false"
            >
              <n-input
                v-model:value="q.options[option_index]"
                placeholder="Add option, press Enter to add more"
                @keydown.enter="addOption(i, option_index)"
                :ref="(el) => (questionRefs[`${i}-${option_index}`] = el)"
              >
                <template #suffix>
                  <n-button text circle @click="addOption(i, option_index)">
                    <template #icon
                      ><n-icon><MdAdd /></n-icon
                    ></template>
                  </n-button>

                  <n-button
                    text
                    circle
                    @click="removeOption(i, option_index)"
                    :disabled="q.options.length <= 1"
                  >
                    <template #icon
                      ><n-icon><MdRemove /></n-icon
                    ></template>
                  </n-button>
                </template>
              </n-input>
            </n-form-item>
          </div>

          <template #action>
            <div class="actions">
              <n-popconfirm @positive-click="removeQuestion(i)">
                <template #trigger>
                  <n-button tertiary type="error">Remove</n-button>
                </template>
                Remove this question?
              </n-popconfirm>
            </div>
          </template>
        </n-card>
      </div>
    </n-form>

    <!-- Add question toolbar -->
    <div class="add-toolbar">
      <n-button @click="addShortText" secondary
        >+ Add Open-ended Question</n-button
      >
      <n-button @click="addMultipleChoice" secondary
        >+ Add Multiple Choice</n-button
      >
      <n-button @click="addSUS" secondary
        >+ Add System Usability Scale</n-button
      >
      <!-- <n-space />
      <n-upload
        :show-file-list="false"
        accept="application/json"
        @change="handleLoadFile"
      >
        <n-button quaternary>Load from JSON</n-button>
      </n-upload>
      <n-button quaternary @click="saveToFile">Save as JSON</n-button> -->
    </div>

    <template #action>
      <div class="card-nav">
        <n-button tertiary @click="nav.prev">
          <n-icon><MdArrowRoundBack /></n-icon> Back
        </n-button>
        <n-space>
          <n-button type="primary" @click="handleNext">
            Next <n-icon><MdArrowRoundForward /></n-icon>
          </n-button>
        </n-space>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { inject, onMounted, ref, computed, nextTick } from "vue";
import { FORM_KEY, NAV_KEY, type WizardForm, type WizardNav } from "../types";
import { MdArrowRoundBack, MdArrowRoundForward } from "@vicons/ionicons4";
import { MdAdd, MdRemove } from "@vicons/ionicons4";
import type { FormInst } from "naive-ui";
type ShortTextQ = {
  uid: number;
  id: string;
  type: "short_text";
  prompt: string;
};
type MultipleChoiceQ = {
  uid: number;
  id: string;
  type: "multiple_choice";
  prompt: string;
  options: string[];
};
type UIQuestion = ShortTextQ | MultipleChoiceQ;
const questionRefs = ref<{
  [key: string]: HTMLInputElement;
}>({});

const form = inject<WizardForm>(FORM_KEY)!;
const nav = inject<WizardNav>(NAV_KEY)!;
const formRef = ref<FormInst>();

// ---------- Local builder state ----------
const questionnaireId = ref<string>("web_shopping_experience_v1");
const title = ref<string>("Untitled Survey");
// const questions = ref<UIQuestion[]>([]);
const questionsForm = ref<{ questions: UIQuestion[] }>({ questions: [] });
let uidCounter = 1;

function nextQuestionId(): string {
  // find max qN in existing, return next
  const nums = questionsForm.value.questions
    .map((q) => /^q(\d+)$/.exec(q.id)?.[1])
    .filter(Boolean)
    .map((n) => Number(n));
  const max = nums.length ? Math.max(...nums) : 0;
  return `q${max + 1}`;
}

function addShortText() {
  questionsForm.value.questions.push({
    uid: uidCounter++,
    id: nextQuestionId(),
    type: "short_text",
    prompt: "",
  });
}
function addMultipleChoice() {
  questionsForm.value.questions.push({
    uid: uidCounter++,
    id: nextQuestionId(),
    type: "multiple_choice",
    prompt: "",
    options: [""],
  });
}
function addSUS() {
  const susStatements = [
    "I think that I would like to use this system frequently. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I found the system unnecessarily complex. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I thought the system was easy to use. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I think that I would need the support of a technical person to be able to use this system. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I found the various functions in this system were well integrated. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I thought there was too much inconsistency in this system. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I would imagine that most people would learn to use this system very quickly. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I found the system very cumbersome to use. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I felt very confident using the system. (1 = Strongly Disagree, 5 = Strongly Agree)",
    "I needed to learn a lot of things before I could get going with this system. (1 = Strongly Disagree, 5 = Strongly Agree)",
  ];
  const likertOptions = [
    "1",
    "2",
    "3",
    "4",
    "5",
  ];
  susStatements.forEach((text) => {
    questionsForm.value.questions.push({
      uid: uidCounter++,
      id: nextQuestionId(),
      type: "multiple_choice",
      prompt: text,
      options: [...likertOptions],
    });
  });
}
function removeQuestion(index: number) {
  questionsForm.value.questions.splice(index, 1);
}

// ---------- Load from existing textarea (if any) ----------
onMounted(() => {
  try {
    const txt = form.survey.questionnaire?.trim();
    if (!txt) return;
    const obj = JSON.parse(txt);
    if (obj?.questionnaire_id)
      questionnaireId.value = String(obj.questionnaire_id);
    if (obj?.title) title.value = String(obj.title);
    if (Array.isArray(obj?.questions)) {
      questionsForm.value.questions = obj.questions.map((raw: any) => {
        const base = {
          uid: uidCounter++,
          id: typeof raw.id === "string" ? raw.id : nextQuestionId(),
          prompt: String(raw.prompt ?? ""),
        };
        if (raw.type === "multiple_choice") {
          return {
            ...base,
            type: "multiple_choice" as const,
            options: Array.isArray(raw.options)
              ? raw.options.map((s: any) => String(s ?? ""))
              : [""],
          };
        }
        return { ...base, type: "short_text" as const };
      });
    }
  } catch (e) {
    // keep defaults; preview will show parse issue if any later
    console.warn("[survey] failed to parse existing questionnaire:", e);
  }
});

// ---------- Build JSON preview & validation ----------
const builtSurvey = computed(() => {
  return {
    questionnaire_id: questionnaireId.value.trim(),
    title: title.value.trim(),
    questions: questionsForm.value.questions.map((q) => {
      if (q.type === "multiple_choice") {
        // strip empty options
        const opts = q.options.map((s) => s?.trim()).filter(Boolean);
        return {
          id: q.id,
          type: "multiple_choice",
          prompt: q.prompt?.trim() ?? "",
          options: opts,
        };
      }
      return {
        id: q.id,
        type: "short_text",
        prompt: q.prompt?.trim() ?? "",
      };
    }),
  };
});

const previewJson = computed(() => JSON.stringify(builtSurvey.value, null, 2));

const isValid = computed(() => {
  if (!builtSurvey.value.questionnaire_id) return false;
  if (!builtSurvey.value.title) return false;
  if (
    !Array.isArray(builtSurvey.value.questions) ||
    builtSurvey.value.questions.length === 0
  )
    return false;
  for (const q of builtSurvey.value.questions) {
    if (!q.prompt) return false;
    if (q.type === "multiple_choice") {
      if (!Array.isArray((q as any).options) || (q as any).options.length < 1)
        return false;
    }
  }
  return true;
});

// ---------- Submit ----------
function handleNext() {
  formRef.value?.validate().then(() => {
    // write pretty JSON back into the shared form
    form.survey.questionnaire = previewJson.value;
    nav.next();
  });
}

async function addOption(index: number, option_index: number) {
  questionsForm.value.questions[index].options.splice(option_index + 1, 0, "");
  // focus on the new input
  await nextTick();
  questionRefs.value[`${index}-${option_index + 1}`]?.focus();
}
async function removeOption(index: number, option_index: number) {
  questionsForm.value.questions[index].options.splice(option_index, 1);
}
</script>

<style scoped>
.meta {
  display: grid;
  gap: 8px;
}
.row {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 12px;
  align-items: center;
}
.label {
  font-weight: 500;
  text-align: right;
}
.q-list {
  display: grid;
  gap: 10px;
}
.q-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 12px;
}
.field {
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sublabel {
  font-size: 12px;
  opacity: 0.75;
  margin-bottom: 4px;
}
.hint {
  font-size: 12px;
  opacity: 0.65;
  margin-top: 4px;
}
.add-toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}
.card-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.my-3 {
  margin: 16px 0;
}
</style>
