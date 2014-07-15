from django.utils.six.moves import http_client
from reviewboard.hostingsvcs.service import HostingService
    RAW_MIMETYPE = 'application/vnd.github.v3.raw'

    REFNAME_PREFIX = 'refs/heads/'
    REFNAME_PREFIX_LEN = len(REFNAME_PREFIX)

            repo_info = self._api_get_repository(
                self._get_repository_owner_raw(plan, kwargs),
                self._get_repository_name_raw(plan, kwargs))
        except Exception as e:
            if six.text_type(e) == 'Not Found':
            rsp, headers = self._json_post(
                    # If we get a Not Found, then the authorization was
                    if six.text_type(e) != 'Not Found':
        url = self._build_api_url(self._get_repo_api_url(repository),
                                  'git/blobs/%s' % revision)

        try:
            return self._http_get(url, headers={
                'Accept': self.RAW_MIMETYPE,
            })[0]
        except (URLError, HTTPError):
            raise FileNotFoundError(path, revision)
        url = self._build_api_url(self._get_repo_api_url(repository),
                                  'git/blobs/%s' % revision)

            self._http_get(url, headers={
                'Accept': self.RAW_MIMETYPE,
            })

        except (URLError, HTTPError):

        url = self._build_api_url(self._get_repo_api_url(repository),
                                  'git/refs/heads')

        try:
            rsp = self._api_get(url)
        except Exception as e:
            logging.warning('Failed to fetch commits from %s: %s',
                            url, e)
            return results

        for ref in rsp:
            refname = ref['ref']

            if refname.startswith(self.REFNAME_PREFIX):
                name = refname[self.REFNAME_PREFIX_LEN:]
                results.append(Branch(id=name,
                                      commit=ref['object']['sha'],
                                      default=(name == 'master')))

        resource = 'commits'
        url = self._build_api_url(self._get_repo_api_url(repository), resource)

        if start:
            url += '&sha=%s' % start

        try:
            rsp = self._api_get(url)
        except Exception as e:
            logging.warning('Failed to fetch commits from %s: %s',
                            url, e)
            return results

        for item in rsp:
            url = self._build_api_url(repo_api_url, 'commits')
            url += '&sha=%s' % revision

            try:
                commit = self._api_get(url)[0]
            except Exception as e:
                raise SCMError(six.text_type(e))
        # Step 2: fetch the "compare two commits" API to get the diff if the
        # commit has a parent commit. Otherwise, fetch the commit itself.
        if parent_revision:
            url = self._build_api_url(
                repo_api_url, 'compare/%s...%s' % (parent_revision, revision))
        else:
            url = self._build_api_url(repo_api_url, 'commits/%s' % revision)

        try:
            comparison = self._api_get(url)
        except Exception as e:
            raise SCMError(six.text_type(e))

        if parent_revision:
            tree_sha = comparison['base_commit']['commit']['tree']['sha']
        else:
            tree_sha = comparison['commit']['tree']['sha']

        files = comparison['files']
        url = self._build_api_url(repo_api_url, 'git/trees/%s' % tree_sha)
        url += '&recursive=1'
        tree = self._api_get(url)
        return self._api_post(url=url,
                              username=client_id,
                              password=client_secret)
        self._api_delete(url=url,
                         headers=headers,
                         username=self.account.username,
                         password=password)
    def _get_api_error_message(self, rsp, status_code):
        """Return the error(s) reported by the GitHub API, as a string

        See: http://developer.github.com/v3/#client-errors
        """
        if 'message' not in rsp:
            msg = _('Unknown GitHub API Error')
        elif ('errors' in rsp and
              status_code == http_client.UNPROCESSABLE_ENTITY):
            errors = [e['message'] for e in rsp['errors'] if 'message' in e]
            msg = '%s: (%s)' % (rsp['message'], ', '.join(errors))
        else:
            msg = rsp['message']

        return msg

    def _http_get(self, url, *args, **kwargs):
        data, headers = super(GitHub, self)._http_get(url, *args, **kwargs)
        self._check_rate_limits(headers)
        return data, headers

    def _http_post(self, url, *args, **kwargs):
        data, headers = super(GitHub, self)._http_post(url, *args, **kwargs)
        self._check_rate_limits(headers)
        return data, headers

    def _check_rate_limits(self, headers):
        rate_limit_remaining = headers.get('X-RateLimit-Remaining', None)

        try:
            if (rate_limit_remaining is not None and
                int(rate_limit_remaining) <= 100):
                logging.warning('GitHub rate limit for %s is down to %s',
                                self.account.username, rate_limit_remaining)
        except ValueError:
            pass

        return '%s?access_token=%s' % (
            '/'.join(api_paths),
            self.account.data['authorization']['token'])
    def _api_get_repository(self, owner, repo_name):
        return self._api_get(self._build_api_url(
            self._get_repo_api_url_raw(owner, repo_name)))

    def _api_get(self, url, *args, **kwargs):
        try:
            data, headers = self._json_get(url, *args, **kwargs)
            return data
        except (URLError, HTTPError) as e:
            self._check_api_error(e)

    def _api_post(self, url, *args, **kwargs):
        try:
            data, headers = self._json_post(url, *args, **kwargs)
            return data
        except (URLError, HTTPError) as e:
            self._check_api_error(e)

    def _api_delete(self, url, *args, **kwargs):
        try:
            data, headers = self._json_delete(url, *args, **kwargs)
            return data
        except (URLError, HTTPError) as e:
            self._check_api_error(e)

    def _check_api_error(self, e):
        data = e.read()

        try:
            rsp = json.loads(data)
        except:
            rsp = None

        if rsp and 'message' in rsp:
            response_info = e.info()
            x_github_otp = response_info.get('X-GitHub-OTP', '')

            if x_github_otp.startswith('required;'):
                raise TwoFactorAuthCodeRequiredError(
                    _('Enter your two-factor authentication code. '
                      'This code will be sent to you by GitHub.'))

            if e.code == 401:
                raise AuthorizationError(rsp['message'])

            raise HostingServiceError(rsp['message'])
        else:
            raise HostingServiceError(six.text_type(e))
