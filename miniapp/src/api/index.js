import { http, uploadFile } from "./request";

export const authApi = {
  me: () => http.get("/auth/me"),
  updateProfile: (data) => http.put("/auth/profile", data),
  uploadAvatar: (filePath) => uploadFile("/auth/avatar", filePath, "file"),
  getGoal: () => http.get("/auth/goal"),
  setGoal: (data) => http.put("/auth/goal", data),
};

export const recordApi = {
  addWeight: (data) => http.post("/records/weight", data),
  listWeight: (params) => http.get("/records/weight", params),
  delWeight: (id) => http.del(`/records/weight/${id}`),

  addMeal: (data) => http.post("/records/meal", data),
  listMeal: (date) => http.get("/records/meal", { date }),
  delMeal: (id) => http.del(`/records/meal/${id}`),

  addExercise: (data) => http.post("/records/exercise", data),
  listExercise: (date) => http.get("/records/exercise", { date }),
  delExercise: (id) => http.del(`/records/exercise/${id}`),
};

export const foodApi = {
  search: (params) => http.get("/foods", params),
  categories: () => http.get("/foods/categories"),
  listCustom: () => http.get("/foods/custom"),
  addCustom: (data) => http.post("/foods/custom", data),
  delCustom: (id) => http.del(`/foods/custom/${id}`),
  exercises: (params) => http.get("/exercises", params),
};

export const statsApi = {
  summary: (date) => http.get("/summary", { date }),
  calendar: (month) => http.get("/summary/calendar", { month }),
  weight: (days) => http.get("/stats/weight", { days }),
  calories: (days) => http.get("/stats/calories", { days }),
  overview: () => http.get("/stats/overview"),
  plan: () => http.get("/stats/plan"),
  analysis: (days) => http.get("/stats/analysis", { days }),
};

export const subscribeApi = {
  config: () => http.get("/subscribe/config"),
  status: () => http.get("/subscribe/status"),
  grant: () => http.post("/subscribe/grant", {}),
  toggle: (enabled) => http.post("/subscribe/toggle", { enabled }),
};
