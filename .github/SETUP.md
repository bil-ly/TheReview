# GitHub Actions Setup Instructions

## Private Submodule Configuration

This repository uses a private Git submodule (`lib/auth`). To allow GitHub Actions to access the private submodule, you need to configure a Personal Access Token (PAT).

### Setup Steps

1. **Create a Personal Access Token (PAT)**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a descriptive name like "Backend CI Submodule Access"
   - Set expiration (recommended: 90 days or 1 year, set a calendar reminder to rotate)
   - Select the following scopes:
     - `repo` (Full control of private repositories)
   - Click "Generate token"
   - **IMPORTANT**: Copy the token immediately (you won't be able to see it again)

2. **Add the Token to Repository Secrets**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `SUBMODULE_ACCESS_TOKEN`
   - Value: Paste the PAT you created
   - Click "Add secret"

3. **Test the Setup**
   - Create a test branch and push it
   - Open a Pull Request to main
   - Check that the PR Checks workflow runs successfully
   - Verify that the submodule is properly checked out

### Optional: Codecov Integration

If you want coverage reports uploaded to Codecov:

1. Go to [codecov.io](https://codecov.io) and sign in with GitHub
2. Add your repository
3. Get the repository token
4. Add it as a repository secret named `CODECOV_TOKEN`

### Troubleshooting

**Problem**: Workflow fails with "submodule authentication failed"
- **Solution**: Verify the PAT has `repo` scope and hasn't expired

**Problem**: Workflow fails with "Resource not accessible by integration"
- **Solution**: Ensure the token is added to repository secrets as `SUBMODULE_ACCESS_TOKEN`

**Problem**: Tests pass locally but fail in CI
- **Solution**: Check that all test dependencies are in `pyproject.toml` under `[dependency-groups].dev`

### Alternative: SSH Deploy Keys (Per-Repository Access)

For more granular access control, you can use SSH deploy keys instead:

1. **Generate an SSH key pair** (on your local machine):
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-backend" -f ~/.ssh/github_actions_submodule
   ```

2. **Add the public key to the submodule repository**:
   - Go to the submodule repo → Settings → Deploy keys
   - Click "Add deploy key"
   - Title: "Backend CI Access"
   - Key: Paste contents of `~/.ssh/github_actions_submodule.pub`
   - Check "Allow write access" if needed (usually not needed for CI)
   - Click "Add key"

3. **Add the private key to the main repository**:
   - Go to main repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `SUBMODULE_SSH_KEY`
   - Value: Paste contents of `~/.ssh/github_actions_submodule` (private key)
   - Click "Add secret"

4. **Update the workflows** to use SSH instead:
   - Add this step before checkout in each workflow:
   ```yaml
   - name: Setup SSH for submodule
     uses: webfactory/ssh-agent@v0.9.0
     with:
       ssh-private-key: ${{ secrets.SUBMODULE_SSH_KEY }}
   ```
   - Remove the `token:` line from checkout steps

### Security Best Practices

- Rotate PATs regularly (set calendar reminders)
- Use fine-grained PATs when possible (currently in beta)
- Never commit tokens or keys to the repository
- Review token usage periodically in GitHub settings
- Use the minimum required permissions for each token
