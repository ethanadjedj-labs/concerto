"""
test_provider_contract.py — Static contract verification for in-repo providers.

Adapted from /tmp/nf-eval/abstraction/test_contract.py to load modules from
backend/concerto/ instead of the scratch abstraction directory.

Verifies that provider_northflank (and provider_digitalocean) satisfy the
ProviderBase contract without making any real network calls.

Run:
    cd /root/concerto/backend
    python -m concerto.test_provider_contract

Expected: all 39 assertions pass, exit 0.
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Stub the prod-only imports so this script runs offline ────────────────────

def _make_stub_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


cf_tunnel_stub = _make_stub_module(
    "concerto.cf_tunnel",
    create_named_tunnel=AsyncMock(return_value={
        "tunnel_id": "stub-tunnel-id",
        "tunnel_token": "stub-tunnel-token",
        "hostname": "stub.concerto.run",
    }),
    destroy_named_tunnel=AsyncMock(return_value=None),
)

db_stub = _make_stub_module(
    "concerto.db",
    update_buyer=AsyncMock(return_value=None),
    upsert_hosted_pool=AsyncMock(return_value=None),
)

provisioner_stub = _make_stub_module(
    "concerto.provisioner",
    provision_droplet=AsyncMock(return_value=("droplet-id", "1.2.3.4", "/key.pem", "pw")),
    destroy_droplet=AsyncMock(return_value=None),
    PLAN_TO_SIZE={"solo": "s-2vcpu-4gb", "pro": "s-2vcpu-8gb"},
)

concerto_stub = _make_stub_module(
    "concerto",
    cf_tunnel=cf_tunnel_stub,
    db=db_stub,
    provisioner=provisioner_stub,
)

sys.modules.setdefault("concerto", concerto_stub)
sys.modules.setdefault("concerto.cf_tunnel", cf_tunnel_stub)
sys.modules.setdefault("concerto.db", db_stub)
sys.modules.setdefault("concerto.provisioner", provisioner_stub)

# ── Load in-repo modules as a synthetic package ───────────────────────────────

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_NAME = "concerto_repo"

_pkg_stub = types.ModuleType(_PACKAGE_NAME)
_pkg_stub.__path__ = [_HERE]
_pkg_stub.__package__ = _PACKAGE_NAME
sys.modules[_PACKAGE_NAME] = _pkg_stub


def _load(short_name: str, filename: str):
    full_name = f"{_PACKAGE_NAME}.{short_name}"
    spec = importlib.util.spec_from_file_location(
        full_name, os.path.join(_HERE, filename)
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PACKAGE_NAME
    sys.modules[full_name] = mod
    sys.modules[short_name] = mod
    setattr(_pkg_stub, short_name, mod)
    spec.loader.exec_module(mod)
    return mod


provider_base = _load("provider_base", "provider_base.py")
provider_do   = _load("provider_digitalocean", "provider_digitalocean.py")
provider_nf   = _load("provider_northflank",   "provider_northflank.py")


# ── Test suite ────────────────────────────────────────────────────────────────

class TestExceptionHierarchy(unittest.TestCase):

    def test_doa_auth_error_is_exception(self):
        self.assertTrue(issubclass(provider_base.DOAuthError, Exception))

    def test_do_credit_error_is_exception(self):
        self.assertTrue(issubclass(provider_base.DOCreditError, Exception))

    def test_droplet_boot_error_is_exception(self):
        self.assertTrue(issubclass(provider_base.DropletBootError, Exception))

    def test_exceptions_share_base(self):
        self.assertTrue(issubclass(provider_base.DOAuthError, provider_base.ProvisionError))
        self.assertTrue(issubclass(provider_base.DOCreditError, provider_base.ProvisionError))
        self.assertTrue(issubclass(provider_base.DropletBootError, provider_base.ProvisionError))

    def test_nf_exports_same_exception_names(self):
        self.assertIs(provider_nf.DOAuthError, provider_base.DOAuthError)
        self.assertIs(provider_nf.DOCreditError, provider_base.DOCreditError)
        self.assertIs(provider_nf.DropletBootError, provider_base.DropletBootError)

    def test_do_exports_same_exception_names(self):
        self.assertIs(provider_do.DOAuthError, provider_base.DOAuthError)
        self.assertIs(provider_do.DOCreditError, provider_base.DOCreditError)
        self.assertIs(provider_do.DropletBootError, provider_base.DropletBootError)

    def test_exceptions_are_instantiable(self):
        e = provider_base.DOAuthError("bad token")
        self.assertIsInstance(e, Exception)
        self.assertEqual(str(e), "bad token")


class TestPlanToSize(unittest.TestCase):

    def _check_plan_to_size(self, module, label: str):
        pts = module.PLAN_TO_SIZE
        self.assertIsInstance(pts, dict, f"{label}.PLAN_TO_SIZE must be dict")
        self.assertIn("solo", pts, f"{label}.PLAN_TO_SIZE must have 'solo' key")
        self.assertIn("pro",  pts, f"{label}.PLAN_TO_SIZE must have 'pro' key")
        self.assertIsInstance(pts["solo"], str, f"{label}.PLAN_TO_SIZE['solo'] must be str")
        self.assertIsInstance(pts["pro"],  str, f"{label}.PLAN_TO_SIZE['pro'] must be str")

    def test_base_plan_to_size_structure(self):
        self._check_plan_to_size(provider_base, "provider_base")

    def test_nf_plan_to_size_structure(self):
        self._check_plan_to_size(provider_nf, "provider_northflank")

    def test_do_plan_to_size_structure(self):
        self._check_plan_to_size(provider_do, "provider_digitalocean")

    def test_do_plan_sizes_match_existing_provisioner(self):
        """DO sizes must match /root/concerto provisioner.py:35–38 exactly."""
        self.assertEqual(provider_do.PLAN_TO_SIZE["solo"], "s-2vcpu-4gb")
        self.assertEqual(provider_do.PLAN_TO_SIZE["pro"],  "s-2vcpu-8gb")

    def test_nf_solo_plan_is_nf_compute_200(self):
        """NF solo plan confirmed from GET /v1/plans (result-billing.md)."""
        self.assertEqual(provider_nf.PLAN_TO_SIZE["solo"], "nf-compute-200")


class TestProvisionDropletSignature(unittest.TestCase):
    """
    Exact signature from audit-coupling.md §7:

    async def provision_droplet(
        do_api_key: str,
        region: str,
        size: str,
        token: str,
        customer_email: str = "",
        mode: Literal["byoc", "hosted", "solo", "pro", "trial"] = "byoc",
    ) -> tuple[str, str, str, str]:
    """

    def _check_provision_sig(self, fn, label: str):
        self.assertTrue(asyncio.iscoroutinefunction(fn), f"{label} must be async")
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())

        for name in ("do_api_key", "region", "size", "token"):
            self.assertIn(name, params, f"{label}: missing param '{name}'")

        self.assertIn("customer_email", params, f"{label}: missing 'customer_email'")
        self.assertIn("mode", params, f"{label}: missing 'mode'")

        ce_param = sig.parameters["customer_email"]
        self.assertEqual(ce_param.default, "", f"{label}: customer_email default must be ''")

        mode_param = sig.parameters["mode"]
        self.assertEqual(mode_param.default, "byoc", f"{label}: mode default must be 'byoc'")

    def test_nf_module_provision_signature(self):
        self._check_provision_sig(provider_nf.provision_droplet, "provider_northflank.provision_droplet")

    def test_do_module_provision_signature(self):
        self._check_provision_sig(provider_do.provision_droplet, "provider_digitalocean.provision_droplet")

    def test_nf_class_provision_signature(self):
        fn = provider_nf.NorthflankProvider.provision_droplet
        self.assertTrue(asyncio.iscoroutinefunction(fn))
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        self.assertIn("api_key", params)
        self.assertIn("region", params)
        self.assertIn("size", params)
        self.assertIn("token", params)
        self.assertIn("customer_email", params)
        self.assertIn("mode", params)


class TestDestroyDropletSignature(unittest.TestCase):
    """
    Exact signature from audit-coupling.md §7:

    async def destroy_droplet(
        api_key: str,
        vps_id: str,
        cf_tunnel_id: str = "",
    ) -> None:
    """

    def _check_destroy_sig(self, fn, label: str):
        self.assertTrue(asyncio.iscoroutinefunction(fn), f"{label} must be async")
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())

        self.assertIn("api_key", params, f"{label}: missing 'api_key'")
        self.assertIn("vps_id", params, f"{label}: missing 'vps_id'")
        self.assertIn("cf_tunnel_id", params, f"{label}: missing 'cf_tunnel_id'")

        cf_param = sig.parameters["cf_tunnel_id"]
        self.assertEqual(cf_param.default, "", f"{label}: cf_tunnel_id default must be ''")

    def test_nf_module_destroy_signature(self):
        self._check_destroy_sig(provider_nf.destroy_droplet, "provider_northflank.destroy_droplet")

    def test_do_module_destroy_signature(self):
        self._check_destroy_sig(provider_do.destroy_droplet, "provider_digitalocean.destroy_droplet")


class TestSuspendResumeSignature(unittest.TestCase):

    def _check_sig(self, fn, label: str):
        self.assertTrue(asyncio.iscoroutinefunction(fn), f"{label} must be async")
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        self.assertIn("api_key", params, f"{label}: missing 'api_key'")
        self.assertIn("vps_id", params, f"{label}: missing 'vps_id'")

    def test_nf_suspend_signature(self):
        self._check_sig(provider_nf.suspend, "provider_northflank.suspend")

    def test_nf_resume_signature(self):
        self._check_sig(provider_nf.resume, "provider_northflank.resume")

    def test_do_suspend_signature(self):
        self._check_sig(provider_do.suspend, "provider_digitalocean.suspend")

    def test_do_resume_signature(self):
        self._check_sig(provider_do.resume, "provider_digitalocean.resume")


class TestDestroyNeverRaises(unittest.TestCase):
    """destroy_droplet must swallow all errors — callers do not catch."""

    def test_nf_destroy_swallows_network_error(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_cm = MagicMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_cm)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_cm.delete = AsyncMock(side_effect=Exception("network error"))

            result = asyncio.run(
                provider_nf.destroy_droplet(
                    api_key="fake-key",
                    vps_id="concerto-abc12345",
                    cf_tunnel_id="",
                )
            )
            self.assertIsNone(result)

    def test_nf_destroy_swallows_empty_vps_id(self):
        result = asyncio.run(
            provider_nf.destroy_droplet(api_key="fake-key", vps_id="")
        )
        self.assertIsNone(result)


class TestNFHelpers(unittest.TestCase):

    def test_service_name_is_nf_safe(self):
        name = provider_nf._service_name("abc123_XYZ")
        self.assertRegex(name, r"^[a-z0-9-]+$")
        self.assertLessEqual(len(name), 63)

    def test_volume_name_is_nf_safe(self):
        name = provider_nf._volume_name("abc123_XYZ")
        self.assertRegex(name, r"^[a-z0-9-]+$")

    def test_stable_url_formula(self):
        url = provider_nf._stable_url("concerto-abc12345")
        self.assertTrue(url.startswith("https://"))
        self.assertIn("--concerto-abc12345--", url)
        self.assertTrue(url.endswith(".code.run"))

    def test_stable_url_is_deterministic(self):
        u1 = provider_nf._stable_url("concerto-abc12345")
        u2 = provider_nf._stable_url("concerto-abc12345")
        self.assertEqual(u1, u2)

    def test_build_env_vars_has_all_required_keys(self):
        env = provider_nf._build_env_vars(
            token="testtoken123",
            public_key="ssh-ed25519 AAAA...",
            safe_email="test@example.com",
            ttyd_password="deadbeef" * 4,
            bearer_token="a" * 64, callback_secret="cs",
            public_url="https://p01--concerto-testtoke--w4lp2d6pgkf6.code.run",
            tunnel_info={"tunnel_token": "tt", "hostname": "h.concerto.run"},
            mode="solo",
        )
        required = [
            "CONCERTO_TOKEN", "CONCERTO_API_BASE", "CONCERTO_CALLBACK_URL",
            "CUSTOMER_EMAIL", "TTYD_PASSWORD", "BEARER_TOKEN", "NF_PUBLIC_URL",
            "TUNNEL_TOKEN", "TUNNEL_HOSTNAME",
            "PLAN", "MAX_PARALLEL_SESSIONS", "RAM_LABEL",
            "SSH_PUBLIC_KEY", "SSH_AUTHORIZED_KEY",
        ]
        for key in required:
            self.assertIn(key, env, f"Missing env var: {key}")

    def test_build_env_vars_pro_ram_label(self):
        env = provider_nf._build_env_vars(
            token="t", public_key="pk", safe_email="",
            ttyd_password="pw", bearer_token="bt", callback_secret="cs",
            public_url="https://p01--x--ns.code.run",
            tunnel_info={}, mode="pro",
        )
        self.assertEqual(env["RAM_LABEL"], "8 GB")
        self.assertEqual(env["MAX_PARALLEL_SESSIONS"], "10")

    def test_build_env_vars_solo_ram_label(self):
        env = provider_nf._build_env_vars(
            token="t", public_key="pk", safe_email="",
            ttyd_password="pw", bearer_token="bt", callback_secret="cs",
            public_url="https://p01--x--ns.code.run",
            tunnel_info={}, mode="solo",
        )
        self.assertEqual(env["RAM_LABEL"], "4 GB")
        self.assertEqual(env["MAX_PARALLEL_SESSIONS"], "3")

    def test_sanitize_email_keeps_plus(self):
        """'+' is valid in email addresses; must not be stripped."""
        result = provider_base.sanitize_email("user+tag@example.com")
        self.assertEqual(result, "user+tag@example.com")

    def test_sanitize_email_strips_dangerous_chars(self):
        result = provider_base.sanitize_email("user$(rm -rf)@evil.com")
        self.assertNotIn("$", result)
        self.assertNotIn("(", result)
        self.assertNotIn(")", result)

    def test_stable_url_port_name_leads(self):
        """URL must start with port name (p01) per proven NF formula."""
        url = provider_nf._stable_url("concerto-abc12345")
        self.assertTrue(url.startswith("https://p01--"), url)

    def test_stable_url_cluster_namespace_suffix(self):
        """URL must end with cluster-namespace.code.run."""
        import importlib
        ns = os.environ.get("CONCERTO_NF_CLUSTER_NAMESPACE", "w4lp2d6pgkf6")
        url = provider_nf._stable_url("concerto-abc12345")
        self.assertTrue(url.endswith(f"--{ns}.code.run"), url)

    def test_public_url_present_in_env_vars(self):
        """NF_PUBLIC_URL in _build_env_vars output must equal _stable_url for same name."""
        svc_name = provider_nf._service_name("tok123abc")
        expected_url = provider_nf._stable_url(svc_name)
        env = provider_nf._build_env_vars(
            token="tok123abc",
            public_key="pk",
            safe_email="e@e.com",
            ttyd_password="pw",
            bearer_token="bt", callback_secret="cs",
            public_url=expected_url,
            tunnel_info={},
            mode="solo",
        )
        self.assertIn("NF_PUBLIC_URL", env)
        self.assertEqual(env["NF_PUBLIC_URL"], expected_url)
        self.assertIn("--" + svc_name + "--", env["NF_PUBLIC_URL"])

    def test_anthropic_key_absent_by_default(self):
        """ANTHROPIC_API_KEY must NOT appear in env when no opt-in."""
        env = provider_nf._build_env_vars(
            token="t", public_key="pk", safe_email="",
            ttyd_password="pw", bearer_token="bt", callback_secret="cs",
            public_url="https://p01--x--ns.code.run",
            tunnel_info={}, mode="solo",
        )
        self.assertNotIn("ANTHROPIC_API_KEY", env)

    def test_anthropic_key_injected_when_explicit(self):
        """ANTHROPIC_API_KEY injected when caller passes it (opt-in path)."""
        env = provider_nf._build_env_vars(
            token="t", public_key="pk", safe_email="",
            ttyd_password="pw", bearer_token="bt", callback_secret="cs",
            public_url="https://p01--x--ns.code.run",
            tunnel_info={}, mode="solo",
            anthropic_api_key="sk-ant-test-key",
        )
        self.assertIn("ANTHROPIC_API_KEY", env)
        self.assertEqual(env["ANTHROPIC_API_KEY"], "sk-ant-test-key")

    def test_anthropic_key_not_injected_when_empty(self):
        """Empty anthropic_api_key must not produce ANTHROPIC_API_KEY key in env."""
        env = provider_nf._build_env_vars(
            token="t", public_key="pk", safe_email="",
            ttyd_password="pw", bearer_token="bt", callback_secret="cs",
            public_url="https://p01--x--ns.code.run",
            tunnel_info={}, mode="solo",
            anthropic_api_key="",
        )
        self.assertNotIn("ANTHROPIC_API_KEY", env)

    def test_callback_url_uses_concerto_api_base(self):
        """CONCERTO_CALLBACK_URL must be constructed from CONCERTO_API_BASE."""
        env = provider_nf._build_env_vars(
            token="t", public_key="pk", safe_email="",
            ttyd_password="pw", bearer_token="bt", callback_secret="cs",
            public_url="https://p01--x--ns.code.run",
            tunnel_info={}, mode="solo",
        )
        self.assertIn("CONCERTO_CALLBACK_URL", env)
        self.assertIn("/api/internal/droplet-ready", env["CONCERTO_CALLBACK_URL"])


class TestProviderBaseIsAbstract(unittest.TestCase):

    def test_cannot_instantiate_base(self):
        with self.assertRaises(TypeError):
            provider_base.ProviderBase()

    def test_nf_provider_is_concrete(self):
        try:
            provider_nf.NorthflankProvider()
        except TypeError as e:
            self.fail(f"NorthflankProvider missing abstract method: {e}")

    def test_do_provider_is_concrete(self):
        try:
            provider_do.DigitalOceanProvider()
        except TypeError as e:
            self.fail(f"DigitalOceanProvider missing abstract method: {e}")

    def test_nf_provider_inherits_base(self):
        self.assertTrue(
            issubclass(provider_nf.NorthflankProvider, provider_base.ProviderBase)
        )

    def test_do_provider_inherits_base(self):
        self.assertTrue(
            issubclass(provider_do.DigitalOceanProvider, provider_base.ProviderBase)
        )


class TestFactoryModule(unittest.TestCase):

    def _load_factory(self, name: str):
        full_name = f"{_PACKAGE_NAME}.{name}"
        spec = importlib.util.spec_from_file_location(
            full_name, os.path.join(_HERE, "provider_factory.py")
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = _PACKAGE_NAME
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_factory_do_mode(self):
        with patch.dict(os.environ, {"CONCERTO_PROVISIONER": "do"}):
            factory = self._load_factory("provider_factory_do_test")
            self.assertTrue(hasattr(factory, "provision_droplet"))
            self.assertTrue(hasattr(factory, "destroy_droplet"))
            self.assertTrue(hasattr(factory, "PLAN_TO_SIZE"))
            self.assertTrue(hasattr(factory, "DOAuthError"))
            self.assertTrue(hasattr(factory, "suspend"))
            self.assertTrue(hasattr(factory, "resume"))

    def test_factory_northflank_mode(self):
        with patch.dict(os.environ, {"CONCERTO_PROVISIONER": "northflank"}):
            factory = self._load_factory("provider_factory_nf_test")
            self.assertTrue(hasattr(factory, "provision_droplet"))
            self.assertTrue(hasattr(factory, "destroy_droplet"))
            self.assertTrue(hasattr(factory, "PLAN_TO_SIZE"))
            self.assertTrue(hasattr(factory, "DOAuthError"))
            self.assertTrue(hasattr(factory, "suspend"))
            self.assertTrue(hasattr(factory, "resume"))

    def test_factory_default_is_do(self):
        """With no env var, default must be DO (safety guarantee)."""
        env = {k: v for k, v in os.environ.items() if k != "CONCERTO_PROVISIONER"}
        with patch.dict(os.environ, env, clear=True):
            factory = self._load_factory("provider_factory_default_test")
            # DO PLAN_TO_SIZE uses DO slugs
            self.assertEqual(factory.PLAN_TO_SIZE["solo"], "s-2vcpu-4gb")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with patch("httpx.AsyncClient") as _mock:
        _mock.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        _mock.return_value.__aexit__ = AsyncMock(return_value=None)

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)
