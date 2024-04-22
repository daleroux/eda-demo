# Ⓐ Ansible EDA demo


[![GitHub License](https://img.shields.io/github/license/daleroux/eda-demo)](https://github.com/daleroux/eda-demo/blob/main/LICENSE)[![Ansible Code of Conduct](https://img.shields.io/badge/Code%20of%20Conduct-Ansible-silver.svg)](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
[![CI](https://github.com/daleroux/eda-demo/actions/workflows/main.yml/badge.svg)](https://github.com/daleroux/eda-demo/actions/workflows/main.yml)

The playbooks / rulebooks are intended for demo purpose of EDA

<!-- TODO| ## Code of Conduct

We follow the [Ansible Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html) in all our interactions within this project.

If you encounter abusive behavior, please refer to the [policy violations](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html#policy-violations) section of the Code for information on how to raise a complaint.
-->

<!-- TODO| ## Maintenance

The current maintainers are listed in the [CODEOWNERS](https://github.com/daleroux/eda-demo/.github/CODEOWNERS)) file. If you have questions or need help, feel free to mention them in the proposals.

To learn how to maintain / become a maintainer of this collection, refer to the [Maintainer guidelines](MAINTAINING.md).
-->

<!-- TODO| ## Tested with Ansible
List the versions of Ansible the collection has been tested with.e
Must match what is in galaxy.yml.
-->

<!-- TODO| ## External requirements
List any external resources the collection depends on, for example minimum versions of an OS, libraries, or utilities.
Do not list other Ansible collections here.
-->

<!-- TODO| ## Supported connections (Optional)
If your collection supports only specific connection types (such as HTTPAPI, netconf, or others), list them here.
-->

<!-- TODO| ## Included content
Galaxy will eventually list the module docs within the UI, but until that is ready, you may need to either describe your plugins etc here, or point to an external docsite to cover that information.
-->

## Using eda-demo

### Step 1: Installing and Configuring HTTPD on a few RHEL/Fedora Linux VMs

Create an **index.html** file under the **/var/www/html** directory with proper permissions so that a curl command on your linux VM's will return a "200 OK". Here's an example of how you can test this:

`% curl -s -o /dev/null -w "%{http_code}" your_linux_vm`

`200` 

Under the bash_script directory in the git repo, you'll find a **monitor_httpd.sh** script, modify the following variables so that it reflects your environment:

**EDA**   <-- your fully qualified EDA controller name.

**SITES** <-- provide the names of your linux_vm's on which httpd is configured and running.  

You then start the **monitor_httpd.sh** script which will scan your VM's at every minute, and display a spinning wheel. 

Stop httpd from running on one of your linux VM's with command:

`% sudo systemctl stop httpd`

The monitor_httpd.sh script will notice httpd is down on that vm and send a curl command containing a payload to your EDA controller.

## Licensing

MIT License

See [LICENSE](https://spdx.org/licenses/MIT.html) to see the full text.
