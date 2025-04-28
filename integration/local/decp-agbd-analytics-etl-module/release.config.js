const { execSync } = require("child_process");

var commitAnalyzerConfig = [
  "@semantic-release/commit-analyzer",
  {
    releaseRules: [ // https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular
      { type: "chore", release: false }, // "chore:" commit message prefix
      { type: "ci", release: false }, // "ci:" commit message prefix
      { type: "docs", release: "patch" }, // "docs:" commit message prefix
      { type: "major", release: "major" }, // "major:" commit message prefix
      { type: "minor", release: "minor" }, // "minor:" commit message prefix
      { type: "patch", release: "patch" }, // "patch:" commit message prefix
      { type: "refactor", release: "patch" }, // "refactor:" commit message prefix
      { type: "style", release: false }, // "style:" commit message prefix
      { type: "test", release: "patch" }, // "test:" commit message prefix
    ],
  },
]

var changelogConfig = [
  "@semantic-release/changelog",
  { changelogFile: "CHANGELOG.md" }
]

var execGetVersion = 'if [[ "$CI_COMMIT_REF_PROTECTED" != "true" && -n "$CI_COMMIT_SHORT_SHA" ]]; then VERSION=${nextRelease.version}+$CI_COMMIT_SHORT_SHA; else VERSION=${nextRelease.version}; fi'
var execSetVersionNpm = "npm version $VERSION --allow-same-version --no-git-tag-version";
var execSetVersionPoetry = "poetry version $VERSION";
var execSetVersionLegacyTxtFiles = "echo $VERSION > version.txt && echo $VERSION > nextversion.txt";
var execConfig = [
  "@semantic-release/exec",
  {
    verifyReleaseCmd: `${execGetVersion} && ${execSetVersionNpm} && ${execSetVersionPoetry} && ${execSetVersionLegacyTxtFiles}`
  },
]

var releaseNotesGeneratorConfig = "@semantic-release/release-notes-generator"

var gitlabConfig = [
  "@semantic-release/gitlab",
  {
    assets: [
      {
        label: "sdist",
        path: "dist/*.tar.gz",
        type: "package",
      },
      {
        label: "wheel (universal)",
        path: "dist/*-py3-none-any.whl",
        type: "package",
      },
    ],
    gitlabUrl: "https://gitlab-tools.swacorp.com",
  },
]

var gitConfig = [
  "@semantic-release/git",
  {
    assets: [
      "CHANGELOG.md",
      "package-lock.json",
      "package.json",
      "pyproject.toml",
    ],
    message: "chore(release): ${nextRelease.version} released\n\n${nextRelease.notes} ",
  },
]

/**
 * Get the name of current branch if it is a dev branch or "invalid"
 *
 * @return {String} The name of the current branch, "invalid", or "undefined".
 */
function getDevBranchName() {
  try {
    let branch = (
      process.env.CI_COMMIT_BRANCH ||
      process.env.CI_COMMIT_REF_NAME ||
      execSync("git branch --show-current").toString().trim()
    );
    console.log(`Current branch: ${branch}`);
    if (branch in ["master", "alpha", "beta"]) {
      console.log(`${branch} branch detected, ignoring dev release channel`);
      return "ignore";
    } else {
      return branch;
    }
  } catch (error) {
    console.log(`failed to get current branch: ${error.message}`);
    return "undefined";
  }
}

module.exports = {
  branches: [
    {
      name: "master",
      channel: "swa-releases"
    },
    {
      name: "alpha",
      channel: "swa-releases",
      prerelease: true
    },
    {
      name: "beta",
      channel: "swa-releases",
      prerelease: true
    },
    {
      name: getDevBranchName(),
      channel: "swa-dev",
      prerelease: "dev",
    },
  ],
  plugins: [
    commitAnalyzerConfig,
    execConfig,
    releaseNotesGeneratorConfig,
    changelogConfig,
    gitConfig,
    gitlabConfig,
  ],
  tagFormat: "${version}",
};
