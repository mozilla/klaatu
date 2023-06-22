const report = require("multiple-cucumber-html-reporter");
const fs = require("fs");

report.generate({
  jsonDir: "/home/b4hand/projects/mozilla/klaatu/tests",
  reportPath: "./cucumber-report",
  metadata: {
    browser: {
      name: "firefox",
      version: "110",
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
      { label: "Project", value: "Custom project" },
      { label: "Release", value: "1.2.3" },
      { label: "Cycle", value: "B11221.34321" },
      { label: "Execution Start Time", value: "Nov 19th 2017, 02:31 PM EST" },
      { label: "Execution End Time", value: "Nov 19th 2017, 02:56 PM EST" },
    ],
  },
});