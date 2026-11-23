import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  pages: { signIn: "/signin" },
  callbacks: {
    // Runs in proxy.ts: only signed-in users get past it.
    authorized({ auth }) {
      return auth !== null;
    },
    // Runs at sign-in: keep Google's permanent account id in the session cookie.
    jwt({ token, profile }) {
      if (profile?.sub) {
        token.googleSub = profile.sub;
      }
      return token;
    },
    session({ session, token }) {
      // The token is untyped, so tell TypeScript what jwt() above stored.
      session.user.googleSub = token.googleSub as string;
      return session;
    },
  },
});
