$adminPassword = $env:POS_TEST_ADMIN_PASSWORD
if (-not $adminPassword) { throw "POS_TEST_ADMIN_PASSWORD is required" }
$loginBody = @{ username = 'admin'; password = $adminPassword } | ConvertTo-Json
$loginResult = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' -Method POST -ContentType 'application/json' -Body $loginBody
$token = $loginResult.access_token
$headers = @{ Authorization = "Bearer $token" }
$result = Invoke-RestMethod -Uri 'http://localhost:8000/api/ai/forecasting/ingredient-forecast' -Headers $headers
Write-Host "Total items:" $result.Count
$result | Select-Object -First 5 | ForEach-Object { Write-Host "$($_.ingredient_name) | Status: $($_.status) | Stock: $($_.current_stock)$($_.unit) | Predicted: $($_.predicted_consumption)$($_.unit) | Shortage: $($_.shortage)$($_.unit)" }
