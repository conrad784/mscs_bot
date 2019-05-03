# Telegram Bot for restarting Minecraft Servers handled with [mscs](https://github.com/MinecraftServerControl/mscs)

## Quickstart
This bot needs `python3`.

1. install requirements
1. initialize config files {token, secret.py}
1. run with `python3 main.py`

## Running as service
This bot should run with the least amount of permissions necessary as it takes user shell input.
Therefore systemd user scripts can be used.
* Enable lingering for user `loginctl enable-linger $USER` to run even if no user session is active.
* Copy `mscs_bot.service` to `~$USER/.config/systemd/user/`.
* Reload systemd `systemctl --user daemon-reload`.
* Then `systemctl --user enable --now mscs_bot.service`.

## Disclaimer
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
