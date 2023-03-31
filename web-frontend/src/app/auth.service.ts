import { Injectable } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpXsrfTokenExtractor
} from '@angular/common/http';
import { Observable, ReplaySubject, Subject, of, BehaviorSubject, throwError, Subscription } from 'rxjs';
import { User, RestService } from "./rest-api";
import { catchError, filter, switchMap, take, tap, map, delay } from 'rxjs/operators';
import {
  CanActivate,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  UrlTree,
  Router,
  ActivatedRoute
} from "@angular/router";
import { CookieService } from "ngx-cookie-service";

@Injectable()
export class HttpXsrfInterceptor implements HttpInterceptor {
  constructor(private tokenExtractor: HttpXsrfTokenExtractor) {
  }
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const cookieheaderName = 'X-Csrftoken';
    let csrfToken = this.tokenExtractor.getToken();
    if (csrfToken !== null && !req.headers.has(cookieheaderName)) {
      req = req.clone({ headers: req.headers.set(cookieheaderName, csrfToken) });
    }
    return next.handle(req);
  }
}

@Injectable({ providedIn: 'root' })
/**
 * token authentication service to login and verify user at backend API
 * access token is regularly rotated (access token lifetime is defined in backend)
 *
 */
export class AuthService {
  user?: User;

  constructor(private rest: RestService, private cookieService: CookieService, private router: Router, private route: ActivatedRoute) {
/*    this.rest.getSession().subscribe(session => {
      if (session.is_authenticated)
        this.user = session.user;
      else
        this.rest.getCsrf().subscribe(res => {
          this.rest.setCsrf(res.headers.get('x-csrftoken') || undefined);
        });
          /!*.subscribe(csrf => {
          this.rest.setCsrf(csrf);
          console.log(csrf)
        })*!/
    });*/
  }

  /**
   * login at backend API with given credentials (username and password)
   *
   * @param credentials
   */
  login(username: string, password: string)  {
    this.rest.login(username, password).subscribe(res => console.log(res))
  }

}
/*

@Injectable({ providedIn: 'root' })
/!**
 * protects routes based on user permissions
 * by default blocks all calls if user is not logged in
 * pass "data" property with entry "expectedRole" (value: admin or dataEditor) to block route from other users
 * role admin includes access to dataEditor pages
 *!/
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService,
              private router: Router) { }

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.authService.getCurrentUser().pipe(
      map(user => {
        const expectedRole = next.data.expectedRole;
        const isLoggedIn = !!user;
        if (expectedRole === 'admin')
          return isLoggedIn && (user?.profile.adminAccess || user?.isSuperuser);
        if (expectedRole === 'dataEditor')
          return isLoggedIn && (user?.profile.canEditBasedata || user?.profile.adminAccess || user?.isSuperuser);
        return isLoggedIn;
      }),
      tap(hasAccess => {
        if (!hasAccess) {
          // @ts-ignore
          const _next = next._routerState.url;
          let params: any = {};
          if (_next && _next !== '/') params['queryParams'] = {next: _next};
          this.router.navigate(['/login'], params);
        }
      })
    );
  }
}
*/
