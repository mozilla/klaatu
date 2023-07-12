const report = require("multiple-cucumber-html-reporter");
const fs = require("fs");

const today = new Date();

report.generate({
  jsonDir: "klaatu/tests",
  reportPath: "./cucumber-report",
  metadata: {
    browser: {
      name: "Firefox",
    },
    device: "Local test machine",
    platform: {
      name: "ubuntu",
      version: "24.04",
    },
  },
  reportName: "Cucumber Report",
  customData: {
    title: "Run info",
    data: [
      { label: "Project", value: "Klaatu Test Report" },
      { label: "Release", value: "1.2.3" },
      { label: "Cycle", value: "B11221.34321" },
      { label: "Execution Start Time", value: today },
    ],
  },
});
