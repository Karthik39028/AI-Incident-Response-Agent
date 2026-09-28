import { useEffect, useState } from "react";
import { ShieldCheck, BrainCircuit, Activity } from "lucide-react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        const response = await fetch(
    "http://localhost:8081/api/auth/github/me",
          {
            method: "GET",
            credentials: "include",
          }
        );

        if (response.ok) {
          const data = await response.json();

          if (data.authenticated) {
            navigate("/dashboard", {
              replace: true,
            });

            return;
          }
        }
      } catch (error) {
        console.error(
          "Authentication check failed:",
          error
        );
      }

      setChecking(false);
    };

    checkAuthentication();
  }, [navigate]);


  const handleGithubLogin = () => {
window.location.href =
    "http://localhost:8081/api/auth/github/login";
  };


  if (checking) {
    return (
      <div className="min-h-screen bg-[#09090b] text-white flex items-center justify-center">
        <div className="text-center">

          <div className="w-10 h-10 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin mx-auto mb-4" />

          <p className="text-sm text-zinc-400">
            Checking authentication...
          </p>

        </div>
      </div>
    );
  }


  return (
    <div className="min-h-screen bg-[#09090b] text-white flex items-center justify-center relative overflow-hidden">

      <div className="absolute inset-0 pointer-events-none">

        <div className="absolute top-[-200px] left-[-150px] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px]" />

        <div className="absolute bottom-[-200px] right-[-150px] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px]" />

      </div>


      <div className="relative z-10 w-full max-w-md px-6">

        <div className="flex justify-center mb-8">

          <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center shadow-2xl">

            <Activity className="w-8 h-8 text-blue-400" />

          </div>

        </div>


        <div className="text-center mb-8">

          <h1 className="text-3xl font-semibold tracking-tight">
            AI SRE Agent
          </h1>

          <p className="text-zinc-400 mt-3 text-sm leading-6">
            Real-time incident response
            <br />
            powered by persistent AI memory
          </p>

        </div>


        <div className="bg-[#111113]/90 border border-white/10 rounded-2xl p-7 shadow-2xl backdrop-blur-xl">

          <div className="mb-6">

            <div className="flex items-center gap-3 mb-2">

              <ShieldCheck className="w-5 h-5 text-emerald-400" />

              <h2 className="font-medium">
                Secure sign in
              </h2>

            </div>

            <p className="text-sm text-zinc-500 leading-6">
              Connect your GitHub account to manage
              applications and incident response.
            </p>

          </div>


          <button
            onClick={handleGithubLogin}
            className="
              w-full
              flex
              items-center
              justify-center
              gap-3
              bg-white
              text-black
              hover:bg-zinc-200
              transition
              rounded-xl
              py-3.5
              font-medium
              cursor-pointer
            "
          >

            <span
              className="
                w-6
                h-6
                rounded-full
                bg-black
                text-white
                flex
                items-center
                justify-center
                text-[10px]
                font-bold
              "
            >
              GH
            </span>

            Continue with GitHub

          </button>


          <div className="mt-7 pt-6 border-t border-white/10">

            <div className="grid grid-cols-2 gap-5">

              <div className="flex gap-3">

                <Activity className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />

                <div>

                  <p className="text-xs font-medium">
                    Real-time monitoring
                  </p>

                  <p className="text-[11px] text-zinc-500 mt-1 leading-4">
                    Detect incidents quickly
                  </p>

                </div>

              </div>


              <div className="flex gap-3">

                <BrainCircuit className="w-4 h-4 text-purple-400 mt-0.5 shrink-0" />

                <div>

                  <p className="text-xs font-medium">
                    Hindsight memory
                  </p>

                  <p className="text-[11px] text-zinc-500 mt-1 leading-4">
                    Learn from past incidents
                  </p>

                </div>

              </div>

            </div>

          </div>

        </div>


        <p className="text-center text-xs text-zinc-600 mt-6">
          AI Incident Response & Learning Agent
        </p>

      </div>

    </div>
  );
}

export default Login;