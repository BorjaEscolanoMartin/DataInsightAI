import { defineRailway, github, project, service } from "railway/iac";
// This repository manages only its own resources in the environment. Other
// repositories export their own partial name.
// See https://docs.railway.com/infrastructure-as-code#multi-repo-projects
export const partial = "DataInsightAI";
export default defineRailway(() => {
  const DataInsightAI = service("DataInsightAI", {
    // dockerfilePath from CaC: "apps/api/Dockerfile"
    // builder from CaC: "DOCKERFILE"
    source: github("BorjaEscolanoMartin/DataInsightAI", { branch: "main", checkSuites: false, rootDirectory: "/apps/api" }),
    start: "bash start.sh",
    healthcheck: "/health",
    replicas: { "us-west2": 1 },
    networking: { privateNetworkEndpoint: "datainsightai" },
  });

  // Celery worker: same image as the API, no healthcheck (it serves no HTTP).
  const worker = service("extraordinary-renewal", {
    source: github("BorjaEscolanoMartin/DataInsightAI", { branch: "main", checkSuites: false, rootDirectory: "/apps/api" }),
    start: "celery -A app.workers.celery_app worker --loglevel=info --concurrency=2",
    replicas: { "us-west2": 1 },
  });

  return project("empathetic-smile", {
    variables: { managed: false },
    resources: [DataInsightAI, worker],
  });
});
